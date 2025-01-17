import logging
import scrapy
import dotenv
import os
import boto3
import json
from datetime import datetime

from scrapy import signals
from scrapy.signalmanager import dispatcher

from listingDescriptionHandler import (
    generate_readable_description,
    generate_readable_title_withAI,
    generate_image_from_AI,
    resize_and_convert_image,
)

dotenv.load_dotenv()


class DealstreamDataSpider(scrapy.Spider):
    name = "dealstream_data"

    # Get today's date in the format YYYYMMDD
    today_date = datetime.now().strftime("%Y%m%d")
    
    custom_settings = {
        "FEED_FORMAT": "json",
        "FEED_URI": f"output/dealstream_{today_date}.json",
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def __init__(self, *args, **kwargs):
        super(DealstreamDataSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        """
        Hook that gets called when the spider is closed. It uploads the generated JSON file to S3.
        """
        file_name = 'output/dealstream.json'
        bucket = os.getenv('OUTPUT_S3_BUCKET_NAME')
        self.upload_to_s3(file_name, bucket)

    # changes the headers and cookies before new run...
    cookies = {
        "cfid": "5ceb9b4c-f18c-4007-a5cc-e8f53bf2d750",
        "cftoken": "0",
        "_gcl_au": "1.1.1293103892.1721724039",
        "__stripe_mid": "c5cc8d7a-5602-4aec-bfb8-80a78949a3aeb106cb",
        "uuid": "E6CCB29E-3663-4D8E-B138D2D4C81CF4DC",
        "hasMembership": "E6CCB29E-3663-4D8E-B138D2D4C81CF4DC",
        "_gid": "GA1.2.329061477.1723608652",
        "_gat_gtag_UA_89671999_1": "1",
        "_ga_N7W2D9NKM5": "GS1.1.1723608651.18.1.1723608670.41.0.0",
        "_ga": "GA1.2.565860145.1721724040",
        "AWSALB": "G7hHuvAkPOMmX6sw4p6/VIIaVx3Gk9Hv1AL3cTBx2VYFit2yC5hpB7bO6w0RIBaZOws4RBH6R341wGkROtGxOxH9/HtKIuuP+JHsN2Egr8cQ/y9fLnAp2n6WhphB",
        "AWSALBCORS": "G7hHuvAkPOMmX6sw4p6/VIIaVx3Gk9Hv1AL3cTBx2VYFit2yC5hpB7bO6w0RIBaZOws4RBH6R341wGkROtGxOxH9/HtKIuuP+JHsN2Egr8cQ/y9fLnAp2n6WhphB",
        "datadome": "kIDDeUKQLuWm~v_onua28NI5t2UIFzzyV9_axq_Mg6oubAMlJI6ulePgx0z2Ji3wJl43FnS4KF8Q3mWZFBLJjRPCYpA7x7aGLSzezpa4CspiJaXYxk9sINPKMlPNysTe",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        # 'cookie': 'cfid=5ceb9b4c-f18c-4007-a5cc-e8f53bf2d750; cftoken=0; _gcl_au=1.1.1293103892.1721724039; __stripe_mid=c5cc8d7a-5602-4aec-bfb8-80a78949a3aeb106cb; uuid=E6CCB29E-3663-4D8E-B138D2D4C81CF4DC; hasMembership=E6CCB29E-3663-4D8E-B138D2D4C81CF4DC; _gid=GA1.2.329061477.1723608652; _gat_gtag_UA_89671999_1=1; _ga_N7W2D9NKM5=GS1.1.1723608651.18.1.1723608670.41.0.0; _ga=GA1.2.565860145.1721724040; AWSALB=G7hHuvAkPOMmX6sw4p6/VIIaVx3Gk9Hv1AL3cTBx2VYFit2yC5hpB7bO6w0RIBaZOws4RBH6R341wGkROtGxOxH9/HtKIuuP+JHsN2Egr8cQ/y9fLnAp2n6WhphB; AWSALBCORS=G7hHuvAkPOMmX6sw4p6/VIIaVx3Gk9Hv1AL3cTBx2VYFit2yC5hpB7bO6w0RIBaZOws4RBH6R341wGkROtGxOxH9/HtKIuuP+JHsN2Egr8cQ/y9fLnAp2n6WhphB; datadome=kIDDeUKQLuWm~v_onua28NI5t2UIFzzyV9_axq_Mg6oubAMlJI6ulePgx0z2Ji3wJl43FnS4KF8Q3mWZFBLJjRPCYpA7x7aGLSzezpa4CspiJaXYxk9sINPKMlPNysTe',
        "priority": "u=0, i",
        "sec-ch-device-memory": "8",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-full-version-list": '"Not)A;Brand";v="99.0.0.0", "Google Chrome";v="127.0.6533.100", "Chromium";v="127.0.6533.100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }

    def start_requests(self):
        # Get the environment variable value
        env_value = os.getenv("RUN_ENV", "local")  # Default to 'local' if not set

        if env_value == "production":

            # Path to the input file
            file_path = "/home/ubuntu/dealstream/input_urls/dealstream_url.txt"
        else:
            # Path to the input file
            file_path = (
                "/Users/vikas/builderspace/dealstream/input_urls/dealstream_url.txt"
            )

        with open(file_path, "r") as file:
            lines = file.readlines()
            # Process each line
            for line in lines:
                url = line.strip()  # Remove any leading/trailing whitespace
                if url:
                    yield scrapy.Request(
                        url,
                        callback=self.parse,
                        headers=self.headers,
                        cookies=self.cookies,
                    )

    def parse(self, response, **kwargs):
        post_cards = response.css(".post")
        for data in post_cards:
            description = data.css("p").xpath("string()").get()
            article_url = f"https://dealstream.com{data.css('h2 a::attr(href)').get()}"
            last_slash_index = article_url.rfind("/")
            ad_id = article_url[last_slash_index + 1 :]
            yield scrapy.Request(
                url=article_url,
                callback=self.parse_next,
                meta={
                    "description": description,
                    "ad_id": ad_id,
                    "article_url": article_url,
                },
                headers=self.headers,
                cookies=self.cookies,
            )

        next_page_url = response.css(
            "div.col-md-6.col-6.text-end a.btn.btn-default.btn-sm::attr(href)"
        ).get()
        if next_page_url:
            next_page = f"https://dealstream.com{next_page_url}"
            yield scrapy.Request(
                url=next_page,
                callback=self.parse,
                headers=self.headers,
                cookies=self.cookies,
            )

    def parse_next(self, response):
        title = response.css('h1[data-translatable="headline"]::text').get()
        details = response.css(".mb-2 span").xpath("string()").extract()
        article_id = response.meta.get('ad_id')
        
        # Extracting Price
        price_str = response.css('p:contains("Price")::text').get()
        logging.debug(f"price_str is: {price_str}")

        price_str = price_str.split('$')[-1].replace(',', '').strip() if price_str else None
        logging.debug(f"price_str is: {price_str}")

        # Extracting Sales
        sales_str = response.css('p:contains("Sales")::text').get()
        sales_str = sales_str.split('$')[-1].replace(',', '').strip() if sales_str else None
        logging.debug(f"sales_str is: {sales_str}")

        # Extracting Cash Flow
        cash_flow_str = response.css('p:contains("Cash Flow")::text').get()
        cash_flow_str = cash_flow_str.split('$')[-1].replace(',', '').strip() if cash_flow_str else None
        logging.debug(f"cash_flow_str is: {cash_flow_str}")

        # Convert the extracted strings to integers
        price = self.convert_to_int(price_str)
        sales = self.convert_to_int(sales_str)
        cash_flow = self.convert_to_int(cash_flow_str)

        ebita = cash_flow

        category = response.css(".b span:nth-child(1)::text").get()
        location = response.css(".b span:nth-child(2)::text").get()

        name = response.css("#main .mb-1 a::text").get()
        person_image = response.css(".borderless::attr(src)").get()
        person_other_info = (
            response.css(".text-info.justify-content-between")
            .xpath("string()")
            .getall()
        )
        scrapedBusinessDescription = response.meta.get("description")

        fullScrapedDescription = self.combine_description_with_details(
            scrapedBusinessDescription, details
        )

        ai_images_dict = {}

        if (
            fullScrapedDescription
            and fullScrapedDescription != "NA"
            and fullScrapedDescription != ""
        ):
            business_description = generate_readable_description(fullScrapedDescription)

            ai_images_dict = generate_image_from_AI(business_description, article_id, title)

        else:
            business_description = fullScrapedDescription

        if (
            business_description
            and business_description != "NA"
            and business_description != ""
        ):
            title = generate_readable_title_withAI(business_description)
        else:
            title = "NA"

        listed_by = {
            "broker-name": name if name else "",
            "broker_image": person_image if name else "",
            "broker_other_info": person_other_info if person_other_info else "",
        }
        dynamic_dict = []
        dynamic_dict.append(ai_images_dict)
        scrapped_image_url = response.css(".listing-photo::attr(src)").get()
        '''
        if scrapped_image_url:
            scrapped_images_dict = {}
            # Sizes you want to resize your image to
            sizes = [(851, 420), (526, 240), (146, 202), (411, 243), (265, 146)]
            s3_object_key = article_id+"_DealStream.png"

            for size in sizes:
                try:
                    resized_s3_url = resize_and_convert_image(scrapped_image_url, size, s3_object_key)
                    key = f"{size[0]}x{size[1]}"
                    scrapped_images_dict[key] = resized_s3_url
                except OSError as e:
                    self.logger.error(f"Error processing image {scrapped_image_url}: {e}")
                    continue
        
            dynamic_dict.append(scrapped_images_dict)
        
            print("dynamic_dict after Scrapped Image Dict", dynamic_dict)

            print("dynamic_dict after Scrapped Image Dict", json.dumps(dynamic_dict))
        '''


        yield {
            "ad_id": f"{article_id}_DealStream",
            "article_url": response.meta.get("article_url"),
            "title": title,
            "source": "dealstream",
            "category": category,
            "location": location,
            "asking_price": price,
            "gross_revenue": sales,
            "cash_flow": cash_flow,
            "EBITDA": ebita,
            'listing-photos': json.dumps(dynamic_dict),
            "businessListedBy": listed_by,
            "scraped_business_description": fullScrapedDescription,
            "business_description": business_description,
            "details": details,
            "broker-phone": "",
            "broker-name": "",
        }

    @staticmethod
    def convert_to_int(value_str):
        if value_str is None:
            logging.debug("Received None input for conversion.")
            return 0
        # Stripping any leading/trailing whitespace and removing commas
        try:
            # Remove commas and extra spaces, then convert to int
            return int(value_str.replace(",", "").strip())
        except ValueError:
            # Log the error and the problematic input for debugging
            logging.error(f"Error converting '{value_str}' to int.")
            return 0


    def combine_description_with_details(self, scraped_description, details):
        parsed_details = self.parse_details(details)
        full_description = (
            scraped_description
            + "\n\n"
            + "\n".join(f"{key}: {value}" for key, value in parsed_details.items())
        )
        return full_description

    def parse_details(self, details):
        """
        Parses business details from a scraped string into a dictionary.

        Args:
            details (list): A list where the first item is a string containing business details separated by line breaks.

        Returns:
            dict: A dictionary of parsed details.
        """
        parsed_details = {}
        try:
            lines = details[0].split("\r")
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    parsed_details[key.strip()] = value.strip()
        except IndexError:
            logging.error("Error parsing details: Index out of range")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {str(e)}")
        return parsed_details


    def upload_to_s3(self, file_name, bucket, object_name=None):
        """
        Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified, file_name is used
        """
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # Upload the file
        s3_client = boto3.client("s3")
        try:
            response = s3_client.upload_file(file_name, bucket, object_name)
        except Exception as e:
            return False
        return True
