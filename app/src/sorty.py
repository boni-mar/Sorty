import random
import os
import sys
import numpy as np
import pygame
import pygame.display
from PIL import Image
import configparser

from src.constants import *
from src.color_utils import *

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

##prebarveni


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
	offset = 10
	x = random.randint(offset, 256 - colorGap)
	y = random.randint(offset, 256 - colorGap)
	z = random.randint(max(x, y)+colorGap, min(256, max(x, y)+2*colorGap))
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
	positions = {}
	for choice in menu:
		render = menuFont.render(choice, False, MENU_COLOR)
		pos = (scWidth//2 - int(menuFont.size(choice)[0])//2, 
			   odsazeni + (spaceBetweenChoices+int(menuFont.size(choice)[1]))*(menu.index(choice)+1))
		screen.blit(render, pos)
		positions[choice.strip('<>')] = pos
	return positions

def draw_title(title, screen, scWidth, odsazeni):
	render = titleFont.render(title, False, TITLE_COLOR)
	screen.blit(render, (scWidth//2 - int(titleFont.size(title)[0])//2, 
			odsazeni))

def draw_controls(text, screen, scHeight, odsazeniy, odsazenix):
	render = scoreFont.render(text, False, MENU_COLOR)
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
def menu():

	##hudba
	pygame.mixer.music.set_volume(0.1)
	pygame.mixer.music.load(SOUND_PATH + '/Menu - Kevin MacLeod - Ambler.mp3')
	pygame.mixer.music.play()

	defaultConfig = config['Default']['default']
	title = 'S o r t y'
	menu = ['<Play>', 'Difficulty', 'Quit']
	controls = 'Controls : Mouse, Arrow Keys, Enter, Esc'
	settings = config.sections()
	settings.remove('Default')
	selected = 0
	settingsSelected = settings.index(defaultConfig)
	# menu states
	menuOn = True
	settingsOn = False
	# output varialbe: True = play the game, False = quit
	play = False
	# variable for getting only one click at a time 
	clicked = False

	while menuOn:

		##loopuj hudbu
		if not pygame.mixer.music.get_busy():
			pygame.mixer.music.play()

		##kresleni
		screen.blit(bg, (0, 0))
		draw_title(title, screen, SCREEN_WIDTH, appleHeight)
		menu_positions = draw_menu(menu, screen, SCREEN_WIDTH, appleHeight*2, appleHeight)
		draw_controls(controls, screen, SCREEN_HEIGHT, appleHeight, appleHeight//3)

		pygame.display.update()

		##input handler
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				menuOn = False
			
			#! trochu jsem to vycucal z prstu
			elif not clicked and event.type == pygame.MOUSEBUTTONDOWN:
				clicked = True
				click.play()
				fontSize = menuFont.size('X')
				for menu_item, position in menu_positions.items():
					if event.pos[0] >= position[0] \
						and event.pos[0] <= position[0] + fontSize[0]*len(menu_item) \
						and event.pos[1] >= position[1] \
						and event.pos[1] <= position[1] + fontSize[1]:
						if menu_item == 'Play':
							play = True
							menuOn = False
						elif menu_item == 'Difficulty':
							settingsOn = True
						elif menu_item == 'Quit':
							menuOn = False
							play = False

			elif event.type == pygame.MOUSEBUTTONUP:
				clicked = False

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
						play = True
						menuOn = False

					#zapni nastaveni
					elif  menu[selected] == '<Difficulty>':
						click.play()
						settingsOn = True

					##vypni se
					elif menu[selected] == '<Quit>':
						click.play()
						menuOn = False

					##neco se nam pokazilo
					else:
						print('something wrong.')
		while settingsOn:
			screen.blit(bg, (0, 0))
			draw_title(title,screen,SCREEN_WIDTH, appleHeight)
			menu_positions = draw_menu(settings,screen, 
				SCREEN_WIDTH, 
				appleHeight*2, 
				appleHeight//2)
			selection(settings, settingsSelected, settingsSelected)
			draw_controls(controls, screen, SCREEN_HEIGHT, appleHeight, appleHeight//3)
			pygame.display.update()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					settingsOn = False
				elif not clicked and event.type == pygame.MOUSEBUTTONDOWN:
					clicked = True
					click.play()
					fontSize = menuFont.size('X')
					for i, (menu_item, position) in enumerate(menu_positions.items()):
						if event.pos[0] >= position[0] \
							and event.pos[0] <= position[0] + fontSize[0]*len(menu_item) \
							and event.pos[1] >= position[1] \
							and event.pos[1] <= position[1] + fontSize[1]:

							selection(settings, settingsSelected, i)
							settingsSelected = i
					config.set('Default', 'Default', settings[settingsSelected].strip('<>'))
					with open(CONFIG_PATH + '/config.ini', 'w') as configFile:
						config.write(configFile)
				elif event.type == pygame.MOUSEBUTTONUP:
					clicked = False
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						menuOn = True
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
						config.set('Default', 'Default', settings[settingsSelected].strip('<>'))
						with open(CONFIG_PATH + '/config.ini', 'w') as configFile:
							config.write(configFile)
	return play

#HLAVNI HERNI FUNKCE
def game(playing, apple):
	gameRunning = True
	##hudba
	pygame.mixer.music.load(SOUND_PATH + '/Game - Kevin MacLeod - Move Forward.mp3')
	pygame.mixer.music.play()

	##tracker pro skore a celkovy pocet utrizenych jablek
	score = 0
	applesOut = 0
	while playing:

		##upleteni kosiku
		basket_array = np.array(basket)
		##cerveny
		red_basket = Image.fromarray(
			shift_hue(basket_array,RED_BASKET_HUE), 'RGBA')
		red_data = red_basket.tobytes()
		##zeleny
		green_basket = Image.fromarray(
			shift_hue(basket_array,GREEN_BASKET_HUE), 'RGBA')
		green_data = green_basket.tobytes()
		##modry
		blue_basket = Image.fromarray(
			shift_hue(basket_array,BLUE_BASKET_HUE), 'RGBA')
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
		MIN_COLOR_GAP = int(config[config['Default']['Default']]['minimalcolorgap'])
		i = 0
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

def main():
	# main loop
    gameRunning = True
    while gameRunning:
        playing = menu()
        gameRunning = game(playing, apple)

    # credits
    print('Beneš entertainment 2020, all rights reserved')
