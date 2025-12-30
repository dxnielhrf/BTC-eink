import os

from PIL import Image, ImageDraw, ImageFont
try:
    from waveshare_epd import epd2in13g
except ImportError:
    pass
from data.plot import Plot
from presentation.observer import Observer
from config.config import config

SCREEN_HEIGHT = 122
SCREEN_WIDTH = 250

FONT_SMALL = ImageFont.truetype(
    os.path.join(os.path.dirname(__file__), os.pardir, 'Roses.ttf'), 8)
FONT_LARGE = ImageFont.truetype(
    os.path.join(os.path.dirname(__file__), os.pardir, 'PixelSplitter-Bold.ttf'), 26)

class Epd2in13g(Observer):

    def __init__(self, observable, mode):
        super().__init__(observable=observable)
        self.epd = self._init_display()
        self.screen_image = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), self.epd.WHITE)
        self.screen_draw = ImageDraw.Draw(self.screen_image)
        self.mode = mode

    def _init_display(self):
        epd = epd2in13g.EPD()
        epd.init()
        epd.Clear()
        return epd

    def form_image(self, prices):
        self.screen_draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=self.epd.WHITE)
        screen_draw = self.screen_draw
        if self.mode == "candle":
            Plot.candle(prices, size=(SCREEN_WIDTH - 45, 93), position=(41, 0), draw=screen_draw, 
                       fill_neg=self.epd.RED, fill_pos=self.epd.BLACK)
        else:
            last_prices = [x[3] for x in prices]
            Plot.line(last_prices, size=(SCREEN_WIDTH - 42, 93), position=(42, 0), draw=screen_draw, 
                     fill=self.epd.BLACK)

        flatten_prices = [item for sublist in prices for item in sublist]
        Plot.y_axis_labels(flatten_prices, FONT_SMALL, (0, 0), (38, 89), draw=screen_draw, fill=self.epd.BLACK)
        screen_draw.line([(10, 98), (240, 98)], fill=self.epd.BLACK)
        screen_draw.line([(39, 4), (39, 94)], fill=self.epd.BLACK)
        screen_draw.line([(60, 102), (60, 119)], fill=self.epd.BLACK)
        
        currency_text = config.currency[:3]
        screen_draw.text((-1, 95), currency_text, font=FONT_LARGE, fill=self.epd.YELLOW)
        
        price_text = Plot.human_format(flatten_prices[len(flatten_prices) - 1], 8, 2)
        text_width = screen_draw.textlength(price_text, font=FONT_LARGE)
        price_position = (((SCREEN_WIDTH - text_width - 60) / 2) + 60, 95)
        screen_draw.text(price_position, price_text, font=FONT_LARGE, fill=self.epd.BLACK)

    def update(self, data):
        self.form_image(data)
        self.epd.display(self.epd.getbuffer(self.screen_image))

    def close(self):
        epd2in13g.epdconfig.module_exit(cleanup=True)