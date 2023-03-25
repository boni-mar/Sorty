import random
import os
import sys
import numpy as np
import pygame
import pygame.display
from PIL import Image
import configparser

from src.constants import *

#DISPLAY
pygame.display.init()
SCREEN_SIZE = pygame.display.list_modes()[0]
SCREEN_WIDTH = SCREEN_SIZE[0]
SCREEN_HEIGHT = SCREEN_SIZE[1]
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.NOFRAME)

#VARy PRO HRU
##umisteni, velikosti
UPPER_BORDER = SCREEN_HEIGHT//(10)
ROW_WIDTH = SCREEN_WIDTH//(10/8)
RESIZE_SCALE = SCREEN_WIDTH/220
BASKET_SIZE = (int(39*RESIZE_SCALE), int(50*RESIZE_SCALE))
BG_SIZE = SCREEN_SIZE
basketWidth = BASKET_SIZE[0]
basketHeight = BASKET_SIZE[1]
APPLE_SIZE = (int(10*RESIZE_SCALE), int(10*RESIZE_SCALE))
appleWidth = APPLE_SIZE[0]
appleHeight = APPLE_SIZE[1]

##load default configuration
config = configparser.ConfigParser()
config.read(CONFIG_PATH + '/config.ini')
defaultConfig = config['Default']['Default']

##rozmisteni pro regulerni a posledni radu
MIN_COLOR_GAP = int(config[defaultConfig]['MinimalColorGap'])
MIN_GAP_BETWEEN_APPLES = appleWidth*2
applesPerLine = int(ROW_WIDTH//(appleWidth+MIN_GAP_BETWEEN_APPLES))
realGapBetweenApples = (ROW_WIDTH-appleWidth*applesPerLine)//(applesPerLine-1) + appleWidth
rowsOfApples = int(APPLE_COUNT//applesPerLine + 1)
applesOnLastLine = APPLE_COUNT%applesPerLine
lastLineGap = (ROW_WIDTH-appleWidth*applesOnLastLine)//(applesOnLastLine-1) + appleWidth

##fonty, mozne texty po dohrani
pygame.font.init()
def font(size):
	return pygame.font.Font(DEFAULT_FONT, size)
titleFont = font(appleHeight*2)
menuFont = font(appleHeight)
scoreFont = font(appleHeight//2)
pygameFont = font(appleHeight//4)

##zvuk
pygame.mixer.pre_init(44100,-16,2, 1024)
pygame.mixer.init()
pygame.mixer.music.set_volume(0.1)
# menu sounds
click = pygame.mixer.Sound(SOUND_PATH + '/Menu - click.wav')
click.set_volume(0.2)
# apple is in the right basket
correct = pygame. mixer.Sound(SOUND_PATH + '/Game - correct.wav')
correct.set_volume(0.05)
# apple is not in the right basket
wrong = pygame. mixer.Sound(SOUND_PATH + '/Game - wrong.wav')
wrong.set_volume(0.05)
# when you get everything right
fanfare = pygame.mixer.Sound(SOUND_PATH + '/Game - Fanfare.wav')

##prace s obrazky
apple = Image.open(IMG_PATH + '/jablko.png').convert('RGBA')
apple = apple.resize(APPLE_SIZE, Image.NEAREST)
basket = Image.open(IMG_PATH + '/kosik.png').convert('RGBA')
basket = basket.resize(BASKET_SIZE, Image.NEAREST)
bg = Image.open(IMG_PATH + '/bg.png').convert('RGBA')
bg = bg.resize(BG_SIZE, Image.NEAREST)
bg = pygame.image.fromstring(bg.tobytes(), bg.size, bg.mode)
applePixels = apple.load()
basketPixels = basket.load()

#CLASSy PRO ULOZENI VICE VARu
class Apple(pygame.sprite.Sprite):
	def __init__(self, defaultx, defaulty, data, rgb, size, sort=False):
		pygame.sprite.Sprite.__init__(self)
		self.defaultpos = (int(defaultx), int(defaulty))
		self.posx = int(defaultx)
		self.posy = int(defaulty)
		self.size = size
		self.data = data
		self.rect = pygame.Rect((self.posx, self.posy), size)
		self.rgb = rgb
		self.main_color = ['r', 'g', 'b'][rgb.index(max(rgb))]
		self.boundToMouse = False
		self.sorted = sort

class OneUseApple(pygame.sprite.Sprite):
	def __init__(self, x, y, size):
		super(pygame.sprite.Sprite, self).__init__()
		self.rect = pygame.Rect((x, y),size)

class Basket(pygame.sprite.Sprite):
	def __init__(self, posx, posy, size, color):
		pygame.sprite.Sprite.__init__(self)
		self.posx = posx
		self.posy = posy
		self.size = size
		self.rect = pygame.Rect((self.posx, self.posy), size)
		self.color = color

class Point(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super(pygame.sprite.Sprite, self).__init__()
		self.rect = pygame.Rect(x, y, 1, 1)

#FUNKCE PRO HRU
def rgb_to_hsv(rgb):
    # Translated from source of colorsys.rgb_to_hsv
    # r,g,b should be a numpy arrays with values between 0 and 255
    # rgb_to_hsv returns an array of floats between 0.0 and 1.0.
    rgb = rgb.astype('float')
    hsv = np.zeros_like(rgb)
    # in case an RGBA array was passed, just copy the A channel
    hsv[..., 3:] = rgb[..., 3:]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb[..., :3], axis=-1)
    minc = np.min(rgb[..., :3], axis=-1)
    hsv[..., 2] = maxc
    mask = maxc != minc
    hsv[mask, 1] = (maxc - minc)[mask] / maxc[mask]
    rc = np.zeros_like(r)
    gc = np.zeros_like(g)
    bc = np.zeros_like(b)
    rc[mask] = (maxc - r)[mask] / (maxc - minc)[mask]
    gc[mask] = (maxc - g)[mask] / (maxc - minc)[mask]
    bc[mask] = (maxc - b)[mask] / (maxc - minc)[mask]
    hsv[..., 0] = np.select(
        [r == maxc, g == maxc], [bc - gc, 2.0 + rc - bc], default=4.0 + gc - rc)
    hsv[..., 0] = (hsv[..., 0] / 6.0) % 1.0
    return hsv

def hsv_to_rgb(hsv):
    # Translated from source of colorsys.hsv_to_rgb
    # h,s should be a numpy arrays with values between 0.0 and 1.0
    # v should be a numpy array with values between 0.0 and 255.0
    # hsv_to_rgb returns an array of uints between 0 and 255.
    rgb = np.empty_like(hsv)
    rgb[..., 3:] = hsv[..., 3:]
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = (h * 6.0).astype('uint8')
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    conditions = [s == 0.0, i == 1, i == 2, i == 3, i == 4, i == 5]
    rgb[..., 0] = np.select(conditions, [v, q, p, p, t, v], default=v)
    rgb[..., 1] = np.select(conditions, [v, v, v, q, p, p], default=t)
    rgb[..., 2] = np.select(conditions, [v, p, t, v, v, q], default=p)
    return rgb.astype('uint8')

##prebarveni
def shift_hue(arr,hout):
    hsv=rgb_to_hsv(arr)
    hsv[...,0]=hout
    rgb=hsv_to_rgb(hsv)
    return rgb

##prebarvi kosik
def change_basket(img, pixels, colour):
	for i in range(img.size[0]):
		for j in range(img.size[1]):
			l = list(pixels[i, j])
			l[0] += colour[0]
			l[1] += colour[1]
			l[2] += colour[2]
			pixels[i, j] = tuple(l)

	data = img.tobytes()

	return data

##vygeneruj barvu pro jablko
def generate_color(apple, pixels, colorGap):
	appleWidth = apple.size[0]
	appleHeight = apple.size[1]
	x = random.randint(0, 256 - colorGap)
	y = random.randint(0, 256 - colorGap)
	z = random.randint(max(x, y)+colorGap, 256)
	listToChoose = [x, y, z]
	r = random.choice(listToChoose)
	listToChoose.remove(r)
	g = random.choice(listToChoose)
	listToChoose.remove(g)
	b = listToChoose[0]

	main_color = pixels[appleWidth//2, appleHeight//2]
	shade_color = pixels[appleWidth//2, appleHeight//(10/9.2)]
	for i in range(apple.size[0]):
		for j in range(apple.size[1]):
			if pixels[i, j] == main_color:
				pixels[i, j] = (r, g, b, 255)
			elif pixels[i, j] == shade_color:
				pixels[i, j] = (r//2, g//2, b//2, 255)

	
	data = apple.tobytes()

	return data, (r,g,b)

#FUNKCE PRO MENU
def draw_menu(menu, screen, scWidth, odsazeni, spaceBetweenChoices):
		for choice in menu:
			render = menuFont.render(choice, False, (240, 240, 240))
			screen.blit(render, (scWidth//2 - int(menuFont.size(choice)[0])//2, 
				odsazeni + (spaceBetweenChoices+int(menuFont.size(choice)[1]))*(menu.index(choice)+1)))

def draw_title(title, screen, scWidth, odsazeni):
	render = titleFont.render(title, False, (15, 15, 15))
	screen.blit(render, (scWidth//2 - int(titleFont.size(title)[0])//2, 
			odsazeni))

def draw_controls(text, screen, scHeight, odsazeniy, odsazenix):
	render = scoreFont.render(text, False, (240, 240, 240))
	screen.blit(render, (odsazenix, scHeight - odsazeniy))

##zpracovava vybrany text		
def selection(menu, indexSelected, indexToSelect):
	menu[indexSelected] = menu[indexSelected].strip('<>')
	menu[indexToSelect] = '<' + menu[indexToSelect] + '>'

##nastavi nastaveni obtiznosti
def setSettings(settings, settingSelected, config):
	newGap = int(config[(settings[settingSelected]).strip('<>')]['MinimalColorGap'])
	return newGap

#HLAVNI FUNKCE MENU
def menu(playing, menuOn, MinColorGap):

	##hudba
	pygame.mixer.music.set_volume(0.1)
	pygame.mixer.music.load(SOUND_PATH + '/Menu - Kevin MacLeod - Ambler.mp3')
	pygame.mixer.music.play()

	title = 'S o r t y'
	menu = ['<Play>', 'Difficulty', 'Quit']
	controls = 'Controls : Arrow Keys, Enter, Esc'
	settings = config.sections()
	settings.remove('Default')
	selected = 0
	settingsSelected = settings.index(defaultConfig)

	while menuOn:

		##loopuj hudbu
		if not pygame.mixer.music.get_busy():
			pygame.mixer.music.play()

		##kresleni
		screen.blit(bg, (0, 0))
		draw_title(title,screen,SCREEN_WIDTH, appleHeight)
		draw_menu(menu,screen, SCREEN_WIDTH, appleHeight*2, appleHeight)
		draw_controls(controls, screen, SCREEN_HEIGHT, appleHeight, appleHeight//3)

		pygame.display.update()

		##input handler
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				menuOn = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					menuOn = False
				elif event.key == pygame.K_DOWN:
					click.play()
					if selected == len(menu)-1:
						selection(menu, selected, 0)
						selected = 0
					else:
						selection(menu, selected, selected+1)
						selected += 1
				elif event.key == pygame.K_UP:
					click.play()
					if selected == 0:
						selection(menu, selected, len(menu)-1)
						selected = len(menu)-1
					else:
						selection(menu, selected, selected-1)
						selected -= 1

				##kdyz se vybere nejaka moznost
				elif event.key == pygame.K_RETURN:

					#zacni hru
					if menu[selected] == '<Play>':
						click.play()
						playing = True
						menuOn = False
						return playing, MinColorGap

					#zapni nastaveni
					elif  menu[selected] == '<Difficulty>':
						click.play()
						settingsOn = True

						while settingsOn:
							screen.blit(bg, (0, 0))
							draw_title(title,screen,SCREEN_WIDTH, appleHeight)
							draw_menu(settings,screen, 
								SCREEN_WIDTH, 
								appleHeight*2, 
								appleHeight//2)
							selection(settings, settingsSelected, settingsSelected)
							draw_controls(controls, screen, SCREEN_HEIGHT, appleHeight, appleHeight//3)
							pygame.display.update()

							for event in pygame.event.get():
								if event.type == pygame.QUIT:
									settingsOn = False
								elif event.type == pygame.KEYDOWN:
									if event.key == pygame.K_ESCAPE:
										settingsOn = False
									elif event.key == pygame.K_DOWN:
										click.play()
										if settingsSelected == len(settings)-1:
											selection(settings, settingsSelected, 0)
											settingsSelected = 0
										else:
											selection(settings, settingsSelected, settingsSelected+1)
											settingsSelected += 1
									elif event.key == pygame.K_UP:
										click.play()
										if settingsSelected == 0:
											selection(settings, settingsSelected, len(settings)-1)
											settingsSelected = len(settings)-1
										else:
											selection(settings, settingsSelected, settingsSelected-1)
											settingsSelected -= 1
									elif event.key == pygame.K_RETURN:
										click.play()
										MinColorGap = MinColorGap - MinColorGap + setSettings(settings, settingsSelected, config)
										config.set('Default', 'Default', settings[settingsSelected].strip('<>'))
										with open(CONFIG_PATH + '/config.ini', 'w') as configFile:
											config.write(configFile)

					##vypni se
					elif menu[selected] == '<Quit>':
						click.play()
						sys.exit()

					##neco se nam pokazilo
					else:
						print('something wrong.')
	return False, MinColorGap

#HLAVNI HERNI FUNKCE
def game(playing, apple, gameRunning):

	##hudba
	pygame.mixer.music.load(SOUND_PATH + '/Game - Kevin MacLeod - Move Forward.mp3')
	pygame.mixer.music.play()

	##tracker pro skore a celkovy pocet utrizenych jablek
	score = 0
	applesOut = 0
	while playing:

		##upletani kosiku
		basket_array = np.array(basket)
		green_hue = (180-70)/360
		red_hue = (180-180)/360
		blue_hue = (180+10)/360
		##cerveny
		red_basket = Image.fromarray(
			shift_hue(basket_array,red_hue), 'RGBA')
		red_data = red_basket.tobytes()
		##zeleny
		green_basket = Image.fromarray(
			shift_hue(basket_array,green_hue), 'RGBA')
		green_data = green_basket.tobytes()
		##modry
		blue_basket = Image.fromarray(
			shift_hue(basket_array,blue_hue), 'RGBA')
		blue_data = blue_basket.tobytes()

		##data pro editovani obrazku
		appleMode = apple.mode
		appleSize = apple.size
		basketMode = basket.mode
		basketSize = basket.size

		##prevedeni upletenych kosiku na objekty pygame
		red_basketImg = pygame.image.fromstring(
			red_data, basketSize, basketMode)
		green_basketImg = pygame.image.fromstring(
			green_data, basketSize, basketMode)
		blue_basketImg = pygame.image.fromstring(
			blue_data, basketSize, basketMode)

		##nechavame uzrat jablka
		i = 0
		j = 0
		apples = []
		odsazeni = int((SCREEN_WIDTH - ROW_WIDTH)//2)
		for r in range(1, rowsOfApples+1):
			if r != rowsOfApples:
				for i in range(applesPerLine):
					data, rgb = generate_color(apple, applePixels, MIN_COLOR_GAP)
					x = odsazeni + i*(realGapBetweenApples)
					y = UPPER_BORDER + appleHeight*(r-1)*1.5
					generatedApple = Apple(x, y, data, rgb, appleSize)
					apples.append(generatedApple)
			else:
				for i in range(applesOnLastLine):
					data, rgb = generate_color(apple, applePixels, MIN_COLOR_GAP)
					x = odsazeni + i*(lastLineGap)
					y = UPPER_BORDER + appleHeight*(r-1)*1.5
					generatedApple = Apple(x, y, data, rgb, appleSize)
					apples.append(generatedApple)

		##nevyuzita promenna pro pripadny load pouzitych jablek
		applesSaveable = apples

		##umisteni kosiku
		spaceBetweenBaskets = int((- odsazeni*2 + SCREEN_WIDTH - 3*basketWidth)//2)
		redBasket = Basket(odsazeni, SCREEN_HEIGHT - basketHeight, basketSize, 'r')
		greenBasket = Basket(odsazeni + basketWidth + spaceBetweenBaskets, SCREEN_HEIGHT - basketHeight, basketSize, 'g')
		blueBasket = Basket(odsazeni + 2*(basketWidth + spaceBetweenBaskets), SCREEN_HEIGHT - basketHeight, basketSize, 'b')
		basketGroup = pygame.sprite.Group(redBasket, greenBasket, blueBasket)

		##list objektu pro kolize -> ovladani mysi
		gameOverApples = tuple(apples)
		appleGroup = pygame.sprite.Group()
		for apple in apples:
			appleGroup.add(apple)

		##hlavni loop
		gameOn = True
		endScreen = False
		while gameOn:
			
			##loopuj hudbu
			if not pygame.mixer.music.get_busy():
				pygame.mixer.music.play()
			
			##kdyz nejsou zadna jablka, tak se prosim vypni
			if applesOut == len(gameOverApples):
				endScreen = True
				gameOn = False

			##kreslime
			screen.blit(bg, (0, 0))

			for k in range(len(apples)):
				appleImg = pygame.image.fromstring(
					apples[k].data, appleSize, appleMode)
				screen.blit(appleImg, 
					(apples[k].posx, apples[k].posy))

			screen.blit(red_basketImg, 
				(odsazeni, SCREEN_HEIGHT - basketHeight))
			screen.blit(green_basketImg, 
				(odsazeni + basketWidth + spaceBetweenBaskets, SCREEN_HEIGHT - basketHeight))
			screen.blit(blue_basketImg, 
				(odsazeni + 2*(basketWidth + spaceBetweenBaskets), SCREEN_HEIGHT - basketHeight))

			pygame.display.update()

			##input handler
			for event in pygame.event.get():

				##vypni se
				if event.type == pygame.QUIT:
					gameRunning = False
					return gameRunning
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						gameRunning = True
						return gameRunning

				##locknuti jablka na mys
				elif event.type == pygame.MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					collisionList = pygame.sprite.spritecollide(Point(pos[0], pos[1]), appleGroup, False)
					if collisionList != []:
						selectedApple = apples[apples.index(collisionList[0])]
						apples[apples.index(collisionList[0])].boundToMouse = True

				##navrat jablka na puvodni pozici, kdyz ho mys pusti
				elif event.type == pygame.MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()
					for apple in apples:
						if apple.boundToMouse:
							appleBasketCollision = pygame.sprite.spritecollide(OneUseApple(apple.posx, apple.posy, apple.size), basketGroup, False)
							if appleBasketCollision != []:
								if selectedApple.main_color == appleBasketCollision[0].color:
									correct.play()
									score += 1
									apple.sorted = True
								else:
									wrong.play()
								apple.boundToMouse = False
								applesOut += 1
								apples.remove(apple)

							apple.posx = apple.defaultpos[0]
							apple.posy = apple.defaultpos[1]
							apple.boundToMouse = False
							appleGroup.update()

				##trackujeme pozici mysi
				elif event.type == pygame.MOUSEMOTION:
					pos = pygame.mouse.get_pos()
					for apple in apples:
						if apple.boundToMouse:
							apple.posx = pos[0] - appleWidth//2
							apple.posy = pos[1] - appleHeight//2
							appleGroup.update()

		##konec hry
		if score == APPLE_COUNT:
			pygame.mixer.music.set_volume(0.05)
			fanfare.play()

		while endScreen:

			##loopuj hudbu
			if not pygame.mixer.music.get_busy():
				pygame.mixer.music.play()

			##kreslime
			screen.blit(bg, (0, 0))

			for k in range(len(gameOverApples)):
				appleSorted = gameOverApples[k].sorted
				color = (0, 0, 0)
				if not appleSorted:
					color = UNSORTED_COLOR
				elif appleSorted:
					color = SORTED_COLOR
				appleImg = pygame.image.fromstring(
					gameOverApples[k].data, appleSize, appleMode)
				text = str(gameOverApples[k].rgb)
				render = pygameFont.render(text, False, color)
				screen.blit(render,(gameOverApples[k].posx + appleWidth//2 - int(pygameFont.size(text)[0])//2, int(gameOverApples[k].posy + appleHeight*1.1)))
				screen.blit(appleImg, 
					(gameOverApples[k].posx, gameOverApples[k].posy))

			screen.blit(red_basketImg, 
				(odsazeni, SCREEN_HEIGHT - basketHeight))
			screen.blit(green_basketImg, 
				(odsazeni + basketWidth + spaceBetweenBaskets, SCREEN_HEIGHT - basketHeight))
			screen.blit(blue_basketImg, 
				(odsazeni + 2*(basketWidth + spaceBetweenBaskets), SCREEN_HEIGHT - basketHeight))

			###resime skore a text po dohrani
			percentCorect = float(score/APPLE_COUNT)
			if percentCorect != 1:
				if 0 <= percentCorect <= 0.25:
					quoteIndex = 0
				elif 0.25 < percentCorect <= 0.5:
					quoteIndex = 1
				elif 0.5 < percentCorect <= 0.75:
					quoteIndex = 2
				else:
					quoteIndex = 3
				quote = QUOTES[quoteIndex]
				only = ''
				if score <= (APPLE_COUNT//2):
					only = 'only '
			else:
				quote = 'YOU WON!'
				only = ''
			scoreText = quote + ' You sorted ' + only + str(score) + ' out of ' + str(applesOut) + ' apples!'
			render = scoreFont.render(scoreText, False, (240, 240, 240))
			screen.blit(render, (SCREEN_WIDTH//2 - int(scoreFont.size(scoreText)[0])//2, appleHeight//2))

			pygame.display.update()

			##input handler
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					gameRunning = False
					return gameRunning
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						gameRunning = True
						return gameRunning

#HLAVNI LOOP
gameRunning = True
while gameRunning:

	playing = False
	menuOn = True

	playing, MIN_COLOR_GAP = menu(playing, menuOn, MIN_COLOR_GAP)
	gameRunning = game(playing, apple, gameRunning)

##CREDITS
print('Beneš entertainment 2020, all rights reserved')
