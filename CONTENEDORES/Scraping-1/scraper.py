import os
import time
import json
import unicodedata
from typing import Dict, List, Optional
from urllib.request import urlopen, Request

# Offline parsing
try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None  # will handle gracefully

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TARGET_URL = "https://cse.izt.uam.mx/index.php/home/preguntas"
TIMEOUT = 25
CLICK_PAUSE = 0.25
EXPAND_WAIT_SECONDS = 8


def is_grid_ready(base_url: str) -> bool:
    for path in ("/status", "/wd/hub/status"):
        try:
            url = base_url.rstrip("/") + path
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=5) as r:
                raw = r.read().decode("utf-8", "ignore")
                data = json.loads(raw or "{}")
                value = data.get("value", data)
                if isinstance(value, dict) and value.get("ready") is True:
                    return True
        except Exception:
            continue
    return False


def wait_for_grid(base_url: str, timeout: int = 90) -> None:
    print(f"Esperando Selenium Grid en {base_url} ...")
    start = time.time()
    while time.time() - start < timeout:
        if is_grid_ready(base_url):
            print("✓ Selenium Grid listo")
            return
        time.sleep(1.0)
    raise TimeoutException(f"Selenium Grid no quedó listo en {timeout}s: {base_url}")


def build_driver() -> webdriver.Remote:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=es-ES")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.set_capability("acceptInsecureCerts", True)

    selenium_hub_url = os.getenv("SELENIUM_HUB_URL", "http://selenium-hub:4444")

    try:
        wait_for_grid(selenium_hub_url, timeout=90)
        driver = webdriver.Remote(
            command_executor=f"{selenium_hub_url}/wd/hub",
            options=chrome_options,
        )
        print("✓ Conexión exitosa con Selenium Grid")
        return driver
    except Exception as e:
        print(f"✗ No se pudo usar Selenium Grid: {e}")

    if os.path.exists("/.dockerenv"):
        raise RuntimeError(
            "Ejecutando en contenedor sin navegador local. Espera al Hub o configura SELENIUM_HUB_URL."
        )

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Driver local iniciado")
        return driver
    except Exception as e2:
        print(f"✗ Error iniciando driver local: {e2}")
        raise


def wait_page_ready(driver: webdriver.Remote, timeout: int = TIMEOUT) -> None:
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, "//h2|//h3"))
    )


def close_cookie_banners(driver: webdriver.Remote) -> None:
    candidates = [
        "//button[contains(translate(., 'ACEPTARACEPTOOKENTENDIDO', 'aceptaraceptookentendido'), 'aceptar')]",
        "//button[contains(translate(., 'ACEPTARACEPTOOKENTENDIDO', 'aceptaraceptookentendido'), 'acepto')]",
        "//button[contains(., 'Entendido') or contains(., 'OK')]",
        "//a[contains(., 'Aceptar') or contains(., 'Aceptar todas')]",
        "//*[@role='button' and (contains(., 'Aceptar') or contains(., 'OK'))]",
    ]
    for xp in candidates:
        try:
            elems = driver.find_elements(By.XPATH, xp)
            for el in elems:
                if el.is_displayed():
                    try:
                        safe_click(driver, el)
                        time.sleep(0.2)
                    except Exception:
                        continue
        except Exception:
            pass


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = " ".join(s.split())
    return s.strip()


def is_displayed_with_text(el) -> bool:
    try:
        return el.is_displayed() and len(el.text.strip()) > 0
    except StaleElementReferenceException:
        return False


def safe_click(driver: webdriver.Remote, el) -> None:
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception:
        pass

    try:
        el.click()
        return
    except (ElementNotInteractableException, ElementClickInterceptedException):
        pass

    try:
        ActionChains(driver).move_to_element(el).pause(0.1).click().perform()
        return
    except Exception:
        pass

    try:
        driver.execute_script("arguments[0].click();", el)
    except Exception as e:
        raise e


def find_candidate_headers(driver: webdriver.Remote) -> List:
    xpaths = [
        "//*[@data-toggle='collapse' or @data-bs-toggle='collapse' or @aria-controls or contains(@class,'accordion') or contains(@class,'panel-title') or contains(@class,'accordion-header')]",
        "//h2 | //h3 | //button | //a",
    ]

    seen = set()
    result = []

    for xp in xpaths:
        for el in driver.find_elements(By.XPATH, xp):
            try:
                if not el.is_displayed():
                    continue
                txt = el.text.strip()
                if len(txt) < 2:
                    try:
                        txt = (el.get_attribute("innerText") or "").strip()
                    except Exception:
                        pass
                if len(txt) < 2:
                    continue
                key = (el.id, normalize_text(txt)[:80])
                if key in seen:
                    continue
                seen.add(key)
                result.append(el)
            except StaleElementReferenceException:
                continue

    unique = []
    seen_texts = set()
    for el in result:
        try:
            t = normalize_text((el.text or "").strip())[:120]
        except Exception:
            t = ""
        if t in seen_texts:
            continue
        seen_texts.add(t)
        unique.append(el)
    return unique


def resolve_click_target(header):
    try:
        child = header.find_element(By.XPATH, ".//button|.//a")
        return child
    except NoSuchElementException:
        pass

    try:
        ancestors = header.find_elements(By.XPATH, "./ancestor::*[self::button or self::a]")
        if ancestors:
            return ancestors[-1]
    except Exception:
        pass

    try:
        role = header.get_attribute("role") or ""
        if "button" in role:
            return header
    except Exception:
        pass

    return header


def wait_for_expansion(driver: webdriver.Remote, header) -> Optional[object]:
    start = time.time()
    before_h = driver.execute_script("return document.body.scrollHeight")
    aria_before = None
    try:
        aria_before = header.get_attribute("aria-expanded")
    except Exception:
        pass

    controlled = None
    try:
        cid = header.get_attribute("aria-controls")
        if cid:
            controlled = driver.find_element(By.ID, cid)
    except Exception:
        controlled = None

    while time.time() - start < EXPAND_WAIT_SECONDS:
        time.sleep(CLICK_PAUSE)

        try:
            if aria_before is not None:
                cur = header.get_attribute("aria-expanded")
                if cur != aria_before or cur == "true":
                    if controlled and is_displayed_with_text(controlled):
                        return controlled

            if controlled and is_displayed_with_text(controlled):
                return controlled

            try:
                sibs = header.find_elements(
                    By.XPATH,
                    "following-sibling::*[self::div or self::section or self::article][contains(@class,'show') or contains(@class,'collapse') or contains(@class,'accordion') or contains(@style,'display') or contains(@class,'content')][1]",
                )
                for s in sibs:
                    if is_displayed_with_text(s) and len((s.text or "").strip()) > 20:
                        return s
            except Exception:
                pass

            now_h = driver.execute_script("return document.body.scrollHeight")
            if now_h and before_h and (now_h - before_h) > 50:
                try:
                    blocks = header.find_elements(By.XPATH, "following-sibling::*[self::div or self::section][1]")
                    if blocks and is_displayed_with_text(blocks[0]):
                        return blocks[0]
                except Exception:
                    pass
        except StaleElementReferenceException:
            break

    return None


def extract_text_from(el) -> str:
    if not el:
        return ""
    try:
        txt = el.text.strip()
        if len(txt) >= 3:
            return txt
    except Exception:
        pass

    try:
        txt = (el.get_attribute("innerText") or "").strip()
        return txt
    except Exception:
        return ""


# -------------------------
# Offline HTML parsing path
# -------------------------
def parse_offline_html(html_path: str) -> Dict[str, str]:
    """Parse saved `pagina_preguntas.html` to extract RLTA accordion headings and contents.

    Returns mapping: section_title -> plain text content.
    """
    if not os.path.isfile(html_path):
        raise FileNotFoundError(html_path)

    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 no está instalado. Instálalo o ejecuta el scraper vía Selenium."
        )

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml") if BeautifulSoup else None
    if soup is None:
        return {}

    content: Dict[str, str] = {}

    # The RLTA structure has pairs: button (header) and panel with matching aria-controls / id
    buttons = soup.select('[data-rlta-element="button"][role="button"][id]')
    for btn in buttons:
        try:
            # Title in <h3 data-rlta-element="heading"> inside the button
            h = btn.select_one('h3[data-rlta-element="heading"]') or btn
            raw_title = h.get_text(strip=True)
            title = normalize_text(raw_title) or "seccion"

            panel_id = btn.get("aria-controls")
            panel = soup.find(id=panel_id) if panel_id else None
            if panel is None:
                # Fallback: next sibling with panel role
                sib = btn.find_next_sibling(attrs={"data-rlta-element": "panel"})
                panel = sib

            if panel is None:
                continue

            # Inner content is under data-rlta-element="panel-content"
            panel_content = panel.select_one('[data-rlta-element="panel-content"]') or panel

            # Extract readable text with newlines
            text = panel_content.get_text("\n", strip=True)
            if not text:
                continue

            content[raw_title or title] = text
        except Exception:
            continue

    # If nothing found with strict selectors, fall back to any h3 followed by a panel
    if not content:
        headings = soup.select('h3[data-rlta-element="heading"]')
        for h in headings:
            try:
                raw_title = h.get_text(strip=True)
                title = normalize_text(raw_title) or "seccion"
                # Try to find closest following panel-content
                panel_content = None
                btn = h.find_parent(attrs={"data-rlta-element": "button"})
                if btn and btn.has_attr("aria-controls"):
                    panel = soup.find(id=btn.get("aria-controls"))
                    if panel:
                        panel_content = panel.select_one('[data-rlta-element="panel-content"]') or panel
                if panel_content is None:
                    # generic fallback: next sibling panel
                    candidate = h.find_parent().find_next_sibling()
                    if candidate:
                        panel_content = candidate
                if panel_content is None:
                    continue
                text = panel_content.get_text("\n", strip=True)
                if text:
                    content[raw_title or title] = text
            except Exception:
                continue

    return content


def main():
    # Prefer fast, deterministic offline parse if the saved HTML exists or env var forces it
    offline_html = os.getenv("OFFLINE_HTML", "pagina_preguntas.html")
    if offline_html and os.path.exists(offline_html):
        print(f"Modo offline: parseando {offline_html} …")
        try:
            content = parse_offline_html(offline_html)
            if not content:
                print("No se encontró contenido con el parser offline. Intentando Selenium…")
            else:
                out_path = "contenido_completo_preguntas.txt"
                with open(out_path, "w", encoding="utf-8") as f:
                    for topic, txt in content.items():
                        f.write(f"{topic}:\n{txt}\n\n")
                print(f"Listo (offline). Revisa {out_path}")
                return
        except Exception as e:
            print(f"Parser offline falló: {e}. Intentando Selenium…")

    # Selenium path as fallback or when OFFLINE_HTML not present
    driver = build_driver()
    try:
        driver.get(TARGET_URL)
        wait_page_ready(driver)
        close_cookie_banners(driver)

        try:
            driver.save_screenshot("pagina_preguntas.png")
            with open("pagina_preguntas.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception:
            pass

        headers = find_candidate_headers(driver)
        print(f"Encontradas {len(headers)} cabeceras potenciales.")

        content: Dict[str, str] = {}
        seen_titles = set()

        for idx, header in enumerate(headers, 1):
            try:
                raw = header.text.strip() or (header.get_attribute("innerText") or "").strip()
            except Exception:
                raw = ""
            title = normalize_text(raw)
            if len(title) < 2:
                title = f"seccion_{idx}"
            if title in seen_titles:
                continue
            seen_titles.add(title)

            print(f"[{idx}/{len(headers)}] Procesando: {raw or title}")

            target = resolve_click_target(header)
            try:
                safe_click(driver, target)
            except Exception as e:
                print(f"  ✗ No se pudo hacer click: {e}")
                continue

            content_el = wait_for_expansion(driver, target)
            if not content_el:
                try:
                    driver.execute_script("arguments[0].click();", target)
                    time.sleep(0.5)
                    content_el = wait_for_expansion(driver, target)
                except Exception:
                    pass

            text = extract_text_from(content_el)
            if not text or len(text) < 5:
                try:
                    backup = header.find_element(By.XPATH, "following-sibling::div[normalize-space()][1]")
                    text = extract_text_from(backup)
                except Exception:
                    pass

            if not text or len(text) < 5:
                text = "No se pudo extraer contenido"

            content[raw or title] = text
            print(f"  ✓ {len(text)} caracteres extraídos")

            try:
                safe_click(driver, target)
                time.sleep(0.1)
            except Exception:
                pass

        out_path = "contenido_completo_preguntas.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            for topic, txt in content.items():
                f.write(f"{topic}:\n{txt}\n\n")

        print(f"Scraping completado. Revisa {out_path}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()