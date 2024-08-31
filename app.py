from flask import Flask, request, jsonify,send_file
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException,NoSuchElementException
import time
from selenium.webdriver.chrome.options import Options
import traceback
import os
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import requests
import base64




app = Flask(__name__)
CORS(app)


def retry_on_stale_element(driver, locator, by=By.ID, retries=5, delay=2):
    for i in range(retries):
        try:
            element = driver.find_element(by, locator)
            return element
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise e


if not os.path.exists('downloads'):
        os.makedirs('downloads')

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--incognito")
    options.add_argument("--disable-gpu")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--headless") 
    prefs = {
        "download.default_directory":  "C:\\Users\\skpre\\Downloads",  
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing_for_trusted_sources_enabled": False,
        "safebrowsing.enabled": False
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    return driver


@app.route('/scrape', methods=['POST'])
def scrape_instagram():
    # Get URL from request
    data = request.json
    instagram_url = data.get('url')

    if not instagram_url:
        return jsonify({'error': 'URL is required'}), 400

    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--incognito")
    options.add_argument("--headless")  # Run headless Chrome
    driver = webdriver.Chrome(options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    try:
        driver.get("https://instavideosave.net/")
        time.sleep(1)  # Wait for the page to load

        # Retry on stale element reference
        forms = retry_on_stale_element(driver, 'form')
        searchbar = retry_on_stale_element(forms, "input", by=By.TAG_NAME)
        button = retry_on_stale_element(forms, "button", by=By.TAG_NAME)

        searchbar.send_keys(instagram_url)
        button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.TAG_NAME, "button"))
        )
        button.click()

        downloads = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "m-2"))
        )

        # Extract the video URL or download link
        download_link = downloads.find_element(By.TAG_NAME, "a").get_attribute('href')

        return jsonify({'video_url': download_link})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        driver.quit()


@app.route('/scrape-audio', methods=['POST'])
def scrape_audio():

    data = request.json
    instagram_url = data.get('url')

    if not instagram_url:
        return jsonify({'error': 'URL is required'}), 400

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    # options.add_argument("--incognito")
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(options=options)

    # Apply stealth to the driver
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    try:
        # Navigate to the audio download page
        driver.get("https://instavideosave.net/audio")
        time.sleep(1)  # Allow the page to load

        # Locate and interact with the search form
        forms = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'form'))
        )

        searchbar = forms.find_element(By.TAG_NAME, "input")
        button = forms.find_element(By.TAG_NAME, "button")

        searchbar.send_keys(instagram_url)

        # Click the search button
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.TAG_NAME, "button"))
        )
        button.click()

        # Wait for the download section to appear
        downloads = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "my-2"))
        )

        # Retrieve the audio download link
        download_link = downloads.find_element(By.TAG_NAME, "a").get_attribute('href')

        return jsonify({'audio_url': download_link})
    
    except StaleElementReferenceException:
        return jsonify({'error': 'Stale Element Reference Exception occurred. Please try again.'}), 500
    except TimeoutException:
        return jsonify({'error': 'Operation timed out. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        driver.quit()



# @app.route('/scrape-photo', methods=['POST'])
# def scrape_photo():
#     data = request.json
#     instagram_url = data.get('url')

#     if not instagram_url:
#         return jsonify({'error': 'URL is required'}), 400

#     options = webdriver.ChromeOptions()
#     options.add_argument("--disable-extensions")
#     options.add_argument("--incognito")
#     options.add_argument("--headless")
#     driver = webdriver.Chrome(options=options)

#     stealth(driver,
#             languages=["en-US", "en"],
#             vendor="Google Inc.",
#             platform="Win32",
#             webgl_vendor="Intel Inc.",
#             renderer="Intel Iris OpenGL Engine",
#             fix_hairline=True,
#     )

#     try:
#         app.logger.info("Navigating to instavideosave.net")
#         driver.get("https://instavideosave.net/photo/")
#         time.sleep(5)  

#         app.logger.info("Locating form elements")
#         forms = driver.find_element(By.TAG_NAME, 'form')
#         searchbar = forms.find_element(By.TAG_NAME, "input")
#         button = forms.find_element(By.TAG_NAME, "button")


#         searchbar.send_keys(instagram_url)
#         app.logger.info(f"Instagram URL {instagram_url} entered")

#         button = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.TAG_NAME, "button"))
#         )
#         button.click()

#         button.click()
#         app.logger.info("Search button clicked")

#         # Explicit wait for download section to be visible
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located((By.CLASS_NAME, "mt-3"))
#         )

#         downloads = driver.find_element(By.CLASS_NAME, "mt-3")
#         img_elements = downloads.find_elements(By.TAG_NAME, "img")
#         if img_elements:
#             download_link = img_elements[0].get_attribute('src')
#             app.logger.info(f"Download link found: {download_link}")
#             return jsonify({'image_url': download_link})
#         else:
#             app.logger.error("No image elements found on the page")
#             return jsonify({'error': 'Failed to find image elements'}), 500

#     except Exception as e:
#         app.logger.error(f"Error scraping photo: {str(e)}")
#         return jsonify({'error': 'Failed to scrape photo'}), 500

#     finally:
#         driver.quit()

@app.route('/scrape-photo', methods=['POST'])
def scrape_photo():
    data = request.json
    instagram_url = data.get('url')

    if not instagram_url:
        return jsonify({'error': 'URL is required'}), 400

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    try:
        app.logger.info("Navigating to instavideosave.net")
        driver.get("https://instavideosave.net/photo/")
        
        app.logger.info("Locating form elements")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )
        form = driver.find_element(By.TAG_NAME, 'form')
        searchbar = form.find_element(By.TAG_NAME, "input")
        button = form.find_element(By.TAG_NAME, "button")

        searchbar.send_keys(instagram_url)
        app.logger.info(f"Instagram URL {instagram_url} entered")

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.TAG_NAME, "button"))
        ).click()
        button.click()

        app.logger.info("Search button clicked")

        # Explicit wait for download section to be visible
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "m-auto"))
        )

        downloads = driver.find_element(By.CLASS_NAME, "m-auto")
        img_elements = downloads.find_elements(By.TAG_NAME, "img")
        if img_elements:
            download_link = img_elements[0].get_attribute('src')
            app.logger.info(f"Download link found: {download_link}")
            return jsonify({'image_url': download_link})
        else:
            app.logger.error("No image elements found on the page")
            return jsonify({'error': 'Failed to find image elements'}), 500

    except Exception as e:
        app.logger.error(f"Error scraping photo: {str(e)}")
        return jsonify({'error': 'Failed to scrape photo'}), 500

    finally:
        driver.quit()


# @app.route('/scrape-photo', methods=['POST'])
# def scrape_photo():
#     data = request.json
#     instagram_url = data.get('url')

#     if not instagram_url:
#         return jsonify({'error': 'URL is required'}), 400

#     options = Options()
#     options.add_argument("--disable-extensions")
#     options.add_argument("--incognito")
#     options.add_argument("--headless")
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

#     try:
#         app.logger.info("Navigating to instavideosave.net")
#         driver.get("https://instavideosave.net/photo/")
#         time.sleep(5)  # Wait for the page to fully load

#         app.logger.info("Locating form elements")
#         forms = driver.find_element(By.TAG_NAME, 'form')
#         searchbar = forms.find_element(By.TAG_NAME, "input")
#         button = forms.find_element(By.TAG_NAME, "button")

#         searchbar.send_keys(instagram_url)
#         app.logger.info(f"Instagram URL {instagram_url} entered")
        
#         button = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.TAG_NAME, "button"))
#         )
#         button.click()
#         app.logger.info("Search button clicked")

#         # Explicit wait for downloads section to be visible
#         WebDriverWait(driver, 15).until(
#             EC.visibility_of_element_located((By.CLASS_NAME, "m-auto"))
#         )

#         time.sleep(10)
#         # Get the HTML content from the elements
#         response = driver.find_elements(By.CLASS_NAME, "m-auto")
       
#         html_content = ''.join([element.get_attribute('outerHTML') for element in response])

#         # Parse the HTML with BeautifulSoup
#         soup = BeautifulSoup(html_content, 'html.parser')

#         # Find all image tags
#         img_tags = soup.find_all('img')

#         # Extract the src attribute from each image tag
#         img_urls = [img['src'] for img in img_tags if 'src' in img.attrs]

#         return jsonify({'image_urls': img_urls})

#     except Exception as e:
#         app.logger.error(f"An error occurred: {e}")
#         return jsonify({'error': 'An error occurred while scraping the photo'}), 500

#     finally:
#         driver.quit()



@app.route('/scrape-facebook', methods=['POST'])
def scrape_facebook():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL not provided"}), 400

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    try:
        driver.get("https://instavideosave.net/facebook")
        time.sleep(1)

        forms = retry_on_stale_element(driver, 'form')
        searchbar = retry_on_stale_element(forms, "input", by=By.TAG_NAME)
        button = retry_on_stale_element(forms, "button", by=By.TAG_NAME)

        searchbar.send_keys(url)
        button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.TAG_NAME, "button"))
        )
        button.click()

        downloads = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "m-2"))
        )

        download_link = downloads.find_element(By.TAG_NAME, "a").get_attribute('href')

        return jsonify({'video_url': download_link})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        driver.quit()

@app.route('/scrape-youtube', methods=['POST'])
def scrape_youtube():
    data = request.json
    youtube_url = data.get('url')
    quality = data.get('quality')
    
    if not youtube_url:
        return jsonify({'error': 'URL is required'}), 400

    driver = create_driver()

    try:
        driver.get("https://ssyoutube.com/")
        time.sleep(5)  # Wait for the page to load

        # Locate the form and its elements
        form = driver.find_element(By.ID, 'main-form')
        searchbar = form.find_element(By.ID, 'id_url')
        button = form.find_element(By.ID, 'search')

        # Enter the YouTube URL and submit the form
        searchbar.send_keys(youtube_url)
        button.click()
        time.sleep(5)

        # Fetch image URL
        try:
            image_element = driver.find_element(By.CSS_SELECTOR, 'div.result-col-thumb img')
            image_url = image_element.get_attribute('src')
        except Exception as e:
            image_url = None
            print(f"Error fetching image URL: {str(e)}")

        if quality:
            download_selector = f'download-mp4-{quality}-audio'
            try:
                download_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, download_selector))
                )
                driver.execute_script("arguments[0].scrollIntoView();", download_element)
                driver.execute_script("arguments[0].click();", download_element)
                time.sleep(30)  # Wait for the download to start
                return jsonify({'message': 'Download initiated successfully', 'image_url': image_url}), 200
            except Exception as e:
                return jsonify({'error': f'Quality option {quality} not found', 'image_url': image_url}), 400

        else:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table'))
            )
            download_links = []
            rows = driver.find_elements(By.CSS_SELECTOR, 'table.table tr')
            for row in rows:
                quality_text = row.find_element(By.CSS_SELECTOR, 'td:first-child span strong').text
                download_url = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute('href')
                download_links.append({'quality': quality_text, 'url': download_url})

            return jsonify({'downloads': download_links, 'image_url': image_url}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        driver.quit()


@app.route('/scrape-twitter', methods=['POST'])
def scrape_twitter():
    data = request.json
    twitter_url = data.get('url')
    
    if not twitter_url:
        return jsonify({'error': 'URL is required'}), 400
    
    driver = create_driver()
    
    try:
        driver.get("https://twittervid.com/")
        time.sleep(5)  # Wait for the page to load

        # Find and fill the form
        searchbar = driver.find_element(By.ID, "tweetUrl")
        button = driver.find_element(By.ID, "loadVideos")
        searchbar.send_keys(twitter_url)
        time.sleep(2)  # Wait for a bit before clicking the button
        button.click()

        # Wait for the download section to be visible
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".thumbnail-div"))
        )
        time.sleep(10)

        # Extract the thumbnail URL
        thumbnail_url = driver.find_element(By.CSS_SELECTOR, ".thumbnail-div img").get_attribute("src")
        
        # Extract video quality options
        quality_divs = driver.find_elements(By.CSS_SELECTOR, "div > button.download-button")
        video_options = []
        for div in quality_divs:
            resolution = div.find_element(By.CSS_SELECTOR, ".resolution-badge").text
            video_url = div.get_attribute("data-media-url")
            filetype = div.find_element(By.CSS_SELECTOR, ".type-text").text
            video_options.append({
                'resolution': resolution,
                'filetype': filetype,
                'url': video_url
            })
        
        # Return video options and the thumbnail URL
        return jsonify({
            'video_options': video_options,
            'thumbnail': thumbnail_url
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        driver.quit()

@app.route('/scrape-twitter-photo', methods=['POST'])
def scrape_twitter_photo():
    data = request.json
    twitter_url = data.get('url')

    if not twitter_url:
        return jsonify({'error': 'URL is required'}), 400

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--headless")
    options.add_argument("--incognito")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    # Apply stealth to the driver
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    try:
        driver.get("https://www.brandbird.app/tools/twitter-image-downloader")
        time.sleep(2)

        searchbar = driver.find_element(By.NAME, "tweet-url")
        searchbar.send_keys(twitter_url)
        time.sleep(2)
        searchbar.send_keys(Keys.RETURN)
        time.sleep(5)

        image_div = driver.find_element(By.CSS_SELECTOR, ".css-140afrn")
        image_img = image_div.find_element(By.TAG_NAME, "img").get_attribute('src')

        time.sleep(10) 

        
        
        return jsonify({'image_url': image_img})

    except TimeoutException:
        return jsonify({'error': 'Operation timed out. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        driver.quit()


@app.route('/freepicdownloader', methods=['POST'])
def freepicdownloader():
    data = request.json
    image_url = data.get('url')

    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400

    driver = create_driver()

    try:
        driver.get("https://freepicdownloader.com/")
        time.sleep(5)

        searchbar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "imageUrl"))
        )
        searchbar.send_keys(image_url)

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".bg-primary"))
        )
        submit_button.click()

        download_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Download']"))
        )
        download_button.click()
        print("Download initiated.")

        a_tags = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href^="data:image"]'))
        )

        images = {}
        for idx, a_tag in enumerate(a_tags):
            image_url = a_tag.get_attribute('href')
            image_data = image_url.split(",")[1]
            images[f"Image_{idx}"] = image_data

        time.sleep(10)

    except TimeoutException:
        return jsonify({'error': 'Element not found within the specified timeout'}), 408

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        time.sleep(30)
        driver.quit()

    return jsonify({'success': 'Images downloaded successfully.', 'images': images}), 200

@app.route('/shutterstock-downloader', methods=['POST'])
def shutterstock_downloader():
    data = request.json
    image_url = data.get('url')

    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400

    driver = create_driver()

    try:
        driver.get("https://steptodown.com/shutterstock-downloader/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.newsletter-form")))

        # Fill out the form
        url_input = driver.find_element(By.NAME, "url")
        url_input.send_keys(image_url)

        # Submit the form
        form = driver.find_element(By.CSS_SELECTOR, "form.newsletter-form")
        form.submit()

        # Wait for the page to update and show the image
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[src^='images/steptodown.com']")))

        # Locate the download link
        download_link = driver.find_element(By.CSS_SELECTOR, "li.watch a.btn")
        download_url = download_link.get_attribute("href")

        # Return the download URL in response
        return jsonify({'download_url': download_url}), 200

    except TimeoutException:
        return jsonify({'error': 'Element not found within the specified timeout'}), 408
    except NoSuchElementException:
        return jsonify({'error': 'Element not found on the page'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(debug=True)
