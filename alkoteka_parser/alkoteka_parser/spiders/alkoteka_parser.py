import json
import time
from typing import Iterable, Dict, Any, List, Optional
from urllib.parse import urlencode
from abc import ABC, abstractmethod
from dataclasses import dataclass

import scrapy
from scrapy import Request
from scrapy.http import Response

@dataclass
class ProductData:
    """Data class для хранения информации о продукте"""
    timestamp: int
    RPC: str
    url: str
    title: str
    marketing_tags: List[str]
    brand: str
    section: List[str]
    price_data: Dict[str, Any]
    stock: Dict[str, Any]
    assets: Dict[str, Any]
    metadata: Dict[str, Any]
    variants: int


class BaseAPIBuilder(ABC):
    """Абстрактный базовый класс для построителей API URL"""

    CITY_UUID = "4a70f9e0-46ae-11e7-83ff-00155d026416"
    BASE_API_URL = "https://alkoteka.com/web-api/v1"

    @abstractmethod
    def build_url(self, *args, **kwargs) -> str:
        pass


class ProductListAPIBuilder(BaseAPIBuilder):
    """Класс для построения URL списка товаров"""

    def build_url(self, category_slug: str, page: int = 1, per_page: int = 20) -> str:
        """Генерирует URL API списка товаров."""
        params = {
            "city_uuid": self.CITY_UUID,
            "page": page,
            "per_page": per_page,
            "root_category_slug": category_slug,
        }
        return f"{self.BASE_API_URL}/product?{urlencode(params)}"


class ProductDetailAPIBuilder(BaseAPIBuilder):
    """Класс для построения URL детальной информации о товаре"""

    def build_url(self, slug: str) -> str:
        """Генерирует URL API карточки товара."""
        return f"{self.BASE_API_URL}/product/{slug}?city_uuid={self.CITY_UUID}"


class ProductParser:
    """Класс для парсинга данных продукта"""

    @staticmethod
    def build_title(product: Dict[str, Any]) -> str:
        """Собирает полное название товара"""
        name = product.get("name", "")
        filter_labels = product.get("filter_labels", [])

        for filter_label in filter_labels:
            if filter_label.get("title"):
                name += f", {filter_label['title']}"
        return name

    @staticmethod
    def get_marketing_tags(product: Dict[str, Any]) -> List[str]:
        """Извлекает маркетинговые теги"""
        marketing_tags = []
        if product.get("new"):
            marketing_tags.append("Новинка")
        if product.get("gift_package"):
            marketing_tags.append("Подарочная упаковка")
        return marketing_tags

    @staticmethod
    def get_brand(product: Dict[str, Any]) -> str:
        """Извлекает бренд товара"""
        brand_name = ""
        description_blocks = product.get("description_blocks", [])

        for block in description_blocks:
            if block.get("code") == "brend" and block.get("values"):
                brand_name = block["values"][0].get("name", "")
                break
        return brand_name

    @staticmethod
    def get_section(product: Dict[str, Any]) -> List[str]:
        """Извлекает разделы категорий"""
        category = product.get("category", {})
        parent_name = category.get("parent", {}).get("name", "") if category.get("parent") else ""
        category_name = category.get("name", "")
        return [parent_name, category_name]

    @staticmethod
    def get_price_data(product: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает данные о ценах"""
        original_price = product.get("prev_price")
        current_price = product.get("price", 0)

        try:
            current_price_float = float(current_price) if current_price is not None else 0.0
            original_price_float = float(original_price) if original_price is not None else current_price_float
        except (ValueError, TypeError):
            current_price_float = 0.0
            original_price_float = 0.0

        has_discount = original_price_float > current_price_float > 0

        sale_tag = ""
        if has_discount:
            discount = int((1 - current_price_float / original_price_float) * 100)
            sale_tag = f"Скидка {discount}%"

        return {
            "current": current_price_float,
            "original": original_price_float if has_discount else current_price_float,
            "sale_tag": sale_tag
        }
    @staticmethod
    def get_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает метаданные товара"""
        meta_dict = {}

        text_blocks = product.get("text_blocks", [])
        meta_dict["__description"] = text_blocks[0].get("content", "") if text_blocks else ""

        article = product.get("vendor_code")
        if article:
            meta_dict["article"] = article

        filter_labels = product.get("filter_labels", [])
        for fl in filter_labels:
            meta_dict[fl.get("filter", "")] = fl.get("title", "")

        return meta_dict

    @staticmethod
    def parse_product(product_data: Dict[str, Any], product_url: str) -> ProductData:
        """Парсит полные данные продукта"""
        product = product_data.get("results", {})

        return ProductData(
            timestamp=int(time.time()),
            RPC=product.get("uuid", ""),
            url=product_url,
            title=ProductParser.build_title(product),
            marketing_tags=ProductParser.get_marketing_tags(product),
            brand=ProductParser.get_brand(product),
            section=ProductParser.get_section(product),
            price_data=ProductParser.get_price_data(product),
            stock={
                "in_stock": int(product.get("quantity_total", 0)) > 0,
                "count": product.get("quantity_total", 0),
            },
            assets={
                "main_image": product.get("image_url", ""),
                "set_images": [],
                "view360": [],
                "video": [],
            },
            metadata=ProductParser.get_metadata(product),
            variants=1,
        )


class AlkotekaDetailSpider(scrapy.Spider):
    name = "alkoteka_spider"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'FEED_FORMAT': 'json',
        'FEED_URI': 'result.json',
        'DOWNLOAD_DELAY': 0.5,
        'ROBOTSTXT_OBEY': False,
    }

    START_URLS = [
        "https://alkoteka.com/catalog/krepkiy-alkogol",
        # "https://alkoteka.com/catalog/slaboalkogolnye-napitki-2",
        # "https://alkoteka.com/catalog/bezalkogolnye-napitki-1"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_api_builder = ProductListAPIBuilder()
        self.detail_api_builder = ProductDetailAPIBuilder()
        self.product_parser = ProductParser()

    def start_requests(self) -> Iterable[Request]:
        """Загружает список товаров из каждой категории."""
        for category_url in self.START_URLS:
            category_slug = category_url.split("/")[-1]
            api_url = self.list_api_builder.build_url(category_slug, page=1)

            yield scrapy.Request(
                url=api_url,
                callback=self.parse_product_list,
                meta={"category_slug": category_slug, "page": 1},
            )

    def parse_product_list(self, response: Response) -> Iterable[Request]:
        """Извлекает `slug` товаров и парсит каждую карточку."""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON from {response.url}")
            return

        products = data.get("results", [])

        for product in products:
            slug = product.get("slug")
            product_url = product.get("product_url")

            if slug and product_url:
                detail_url = self.detail_api_builder.build_url(slug)
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_product_detail,
                    meta={"product_url": product_url}
                )

        if data.get("meta", {}).get("has_more_pages"):
            next_page = response.meta["page"] + 1
            next_api_url = self.list_api_builder.build_url(
                category_slug=response.meta["category_slug"],
                page=next_page,
            )

            yield scrapy.Request(
                url=next_api_url,
                callback=self.parse_product_list,
                meta={
                    "category_slug": response.meta["category_slug"],
                    "page": next_page
                },
            )

    def parse_product_detail(self, response: Response) -> Iterable[Dict[str, Any]]:
        """Парсит полные данные из карточки товара."""
        try:
            product_data = json.loads(response.text)
            product = self.product_parser.parse_product(
                product_data,
                response.meta["product_url"]
            )
            yield product.__dict__

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse product detail from {response.url}: {e}")
