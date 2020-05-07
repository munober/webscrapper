from selenium import webdriver
import time, random


def fetch_image_urls_google(
    query: str,
    max_links_to_fetch: int,
    wd: webdriver,
    sleep_between_interactions: 1,
    search_url: str = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img&tbs=sur:fc",
):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    print(f"Searching on google for: {query}")
    wd.get(search_url.format(q=query))
    timeout = True
    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        try:
            scroll_to_end(wd)
            thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")

            pictures = random.sample(range(len(thumbnail_results)), len(thumbnail_results))
            thumbnail_results = [thumbnail_results[i] for i in pictures]  # shuffling list randomly

            if max_links_to_fetch > len(thumbnail_results):
                max_links_to_fetch = len(thumbnail_results)
            number_results = len(thumbnail_results)
            print(
                f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}"
            )
            for img in thumbnail_results[results_start:number_results]:
                try:
                    img.click()
                    time.sleep(sleep_between_interactions)
                except Exception:
                    continue

                # extracting urls
                actual_images = wd.find_elements_by_css_selector("img.n3VNCb")
                for actual_image in actual_images:
                    if actual_image.get_attribute(
                        "src"
                    ) and "http" in actual_image.get_attribute("src"):
                        image_urls.add(actual_image.get_attribute("src"))
                        print(f"{query}: {str(len(image_urls))}/{max_links_to_fetch}")

                image_count = len(image_urls)
                if len(image_urls) >= max_links_to_fetch:
                    print(f"Found: {len(image_urls)} image links, done!")
                    break
            else:
                if timeout:
                    timeout = False
                    print(
                        "Found:", len(image_urls), "image links, looking for more ..."
                    )
                    time.sleep(5)
                    load_more_button = wd.find_element_by_css_selector(".mye4qd")
                    if load_more_button:
                        wd.execute_script("document.querySelector('.mye4qd').click();")
                else:
                    break

            results_start = len(thumbnail_results)
        except Exception as e:
            continue

    return image_urls
