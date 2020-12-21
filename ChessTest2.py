# Play chess against callum
# 1. Open Window
# 2. Navigate to page
# 3. Download screenshot of board

from __future__ import print_function

from playsound import playsound
playsound('shutter.mp3')

import sys
import time
import numpy
import os.path
import pywinauto
import win32api
import pyscreenshot as ImageGrab
import math
import random

import cv2
from PIL import Image
from PIL import ImageChops
from matplotlib import pyplot as plt

import chess
import chess.engine
engine = chess.engine.SimpleEngine.popen_uci("stockfish")

############## CONTROL
FIRST_MOVE = True
moveTimings = [0.5, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 9]
moveCounter = 0

############## PIXEL DATA #110% zoom and challenge
board_px_orig_x = 425
board_px_orig_y = 210
square_length = 650
square_increment = square_length/8
half_square = int(square_increment/2)

############## GET IMAGES
imageDict = {}

MyMovePath = 'MyMove.png'

############### SETUP
web_address = "https://www.chess.com/play/online"
#web_address = "https://www.chess.com/play/computer"

app = pywinauto.Application().start(
    r"c:\Program Files (x86)\Google\Chrome\Application\Chrome.exe {}".format(web_address))
time.sleep(3.5)



####################### ACTUAL FUNCTIONS
def makeMove(raw):
    # take in the 4 letter format
    # raw chess coordinates
    orig_x = (ord(raw[0]) - 96)
    orig_y = 9 - int(raw[1])
    dest_x = (ord(raw[2]) - 96)
    dest_y = 9 - int(raw[3])

    print(orig_x, orig_y, "->", dest_x, dest_y)

    #to pixels in a 0,0 array
    orig_x_px = int((orig_x - 0.5) * square_increment) + board_px_orig_x
    orig_y_px = int((orig_y - 0.5) * square_increment) + board_px_orig_y
    dest_x_px = int((dest_x - 0.5) * square_increment) + board_px_orig_x
    dest_y_px = int((dest_y - 0.5) * square_increment) + board_px_orig_y

    #offset
    origin = [orig_x_px, orig_y_px]
    destination = [dest_x_px, dest_y_px]
    print(origin, destination)
    executeMove(origin, destination)


def executeMove(orig, dest):
    # move piece process
    delay = random.choice(moveTimings)
    print("time delay is ", delay)
    #time.sleep(delay)
    pywinauto.mouse.click(button='left', coords=orig)
    pywinauto.mouse.press(button='left', coords=dest)
    im1 = ImageGrab.grab(bbox=(board_px_orig_x, board_px_orig_y, board_px_orig_x + square_length, board_px_orig_y + square_length))  # X1,Y1,X2,Y2
    im1.save(MyMovePath)


def findMove():
    # set counter for resUP
    global moveCounter
    moveCounter += 1

    move_found = compareImages(MyMovePath)
    while not move_found:
        print ("ERROR images are the same, trying again")
        time.sleep(1.5)
        move_found = compareImages(MyMovePath)

    #find the opponents move origin
    cv2_px = cv2Move("OpMove.png", "pieceImages\Highlight.png", 0.97)
    chess_str_1 = PxtoGrid(cv2_px[0], cv2_px[1])

    #find the corresponding piece move
    chess_square_index = chess.parse_square(chess_str_1)
    if board.piece_at(chess_square_index) is None:
        playsound('Warning.mp3')
        Op_piece_moved = input("Base move missed, what square did it originate from:")
        time.sleep(3)
    else:
        Op_piece_moved = board.piece_at(chess_square_index).symbol().lower()
    print (str(Op_piece_moved))
    print(Op_piece_moved, "was moved by opponent with comparison file at ", imageDict[Op_piece_moved][0])

    targetPath = "pieceImages\\" + imageDict[Op_piece_moved][0]
    cv2_px = cv2Move("OpMove.png", targetPath, imageDict[Op_piece_moved][1])
    chess_str_2 = PxtoGrid(cv2_px[0], cv2_px[1])
    full_str = chess_str_1 + chess_str_2
    print('Resolved string', full_str)
    return full_str



def PxtoGrid(x, y):
    # add half a grid and origin offset
    x += half_square
    y += half_square

    grid_x = int(math.ceil(x/square_increment))
    grid_y = 9 - int(math.ceil(y/square_increment))

    #print("MCGRIDDLE STRING", grid_x, grid_y)
    letter = str(chr(grid_x + 96)) # will print "A"
    print("Letter", letter, grid_y)
    chess_encoded_location = letter + str(grid_y)
    print(chess_encoded_location)
    return(chess_encoded_location)

    # divide by board thing and round down


    #print coords
def cv2Move(image_path, template_path, threshold):
    opPathName = "chessmoves/OpponentMove_"+ str(moveCounter) + ".png"

    img_rgb = cv2.imread(image_path, cv2.IMREAD_COLOR)
    template = cv2.imread(template_path,  cv2.IMREAD_COLOR)
    print(template.shape)

    #w, h, _ = template.shape[::]
    w, h, _ = template.shape

    res = cv2.matchTemplate(img_rgb,template, cv2.TM_CCORR_NORMED)
    #threshold = 0.97

    loc = numpy.where( res >= threshold)

    for pt in zip(*loc[::-1]):
        #print(pt[0], pt[1])
        cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2)

    cv2.imwrite(opPathName, img_rgb)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if max_val < threshold:
        print("object not found")
        sys.exit()
    else:
        return (max_loc)  

def compareImages(MyMove):
    im2 = ImageGrab.grab(bbox=(board_px_orig_x, board_px_orig_y, board_px_orig_x + square_length, board_px_orig_y + square_length)) 
    im2.save('OpMove.png')

    im1_1 = Image.open(MyMove)
    im2_2 = Image.open("OpMove.png")
    diff = ImageChops.difference(im1_1, im2_2)
    if diff.getbbox():
        print("images are different")
        time.sleep(1.5)
        im2 = ImageGrab.grab(bbox=(board_px_orig_x, board_px_orig_y, board_px_orig_x + square_length, board_px_orig_y + square_length)) 
        im2.save('OpMove.png')
        return True
    else:
        print("images are the same")
        return False

########### MAIN
#### Only opening if white
playColour = input('Are you white or black? (W/B): ').lower()
if playColour == 'w':
    board = chess.Board()
    print(board)
    print("Loading black pieces for opponent, focus board")
    FIRST_MOVE = True
    imageDict = {
    'p': ['HighlightPBlackDark.png', 0.85],
    'r': ['HighlightRBlackLight.png', 0.85],
    'n': ['HighlightNBlackDark.png', 0.85],
    'b': ['HighlightBBlackLight.png', 0.85],
    'q': ['HighlightQBlackLight.png',0.85],
    'k': ['HighlightKBlackDark.png', 0.85]
}
    # change dict to black pieces
elif playColour == 'b':
    board = chess.Board().transform(chess.flip_horizontal)
    print(board)
    board.apply_mirror()
    print(board)
    print("Loading white pieces for opponent, focus board")
    FIRST_MOVE = False
    imageDict = {
    'p': ['HighlightPWhiteLight.png', 0.85],
    'r': ['HighlightRWhite.png', 0.85],
    'n': ['HighlightNWhite.png', 0.85],
    'b': ['HighlightBWhite.png', 0.85],
    'q': ['HighlightQWhite.png',0.85],
    'k': ['HighlightKWhite.png', 0.85]
}
    # change dict to white pieces
else:
    print("unrecognized input, ending program")
    sys.exit()
time.sleep(2)

#boardfind()
#cursor_reader()
#cursor_photographer()

#pywinauto.mouse.click(button='left', coords=(board_px_orig_x + 245 + half_square, board_px_orig_y + 84 + half_square))
#print("space test")
#time.sleep(3)

############ LOCATE BOARD
full_screen = ImageGrab.grab(bbox=None) 
print ("locating board...")
full_screen.save('FullScreen.png')
playsound('shutter2.mp3')
if playColour == 'w':
    FullBoardColourPath = 'FullBoard.png'
else:
    FullBoardColourPath = 'FullBoardBlack.png'
board_loc = cv2Move('FullScreen.png', FullBoardColourPath, 0.94)
print("board location: ", board_loc)
board_px_orig_x = board_loc[0]
board_px_orig_y = board_loc[1]
square_length = 715
square_increment = square_length/8
half_square = int(square_increment/2)

############ M MOVE INITIALLY
if FIRST_MOVE:
    makeMove("e2e4")
    move = chess.Move.from_uci("e2e4")
    board.push(move)
else:
    MyMovePath = 'FullBoardBlack.png'
    ######################## GET MOVE
    op_Move = input("What move did they make first: ")
    MyMovePath = 'MyMove.png'
    print("Found move,", op_Move)
    move = chess.Move.from_uci(op_Move)
    board.push(move)

    ####################### MAKE MOVE
    result = engine.play(board, chess.engine.Limit(time=1.0))
    print("1")
    board.push(result.move)
    print("2")
    makeMove(result.move.uci()) #immediately take a photo
    
    print(result.move.uci())
    print(board)
    time.sleep(2)
    ## Start before they move

while not board.is_game_over():
    #Typed_Op_Move = input("Type their move: ")
    #time.sleep(2)

    ######################## GET MOVE
    op_Move = findMove()
    MyMovePath = 'MyMove.png'
    print("Found move,", op_Move)
    move = chess.Move.from_uci(op_Move)
    if move in board.pseudo_legal_moves:
        print('found move is legal')
        board.push(move)
    else:
        playsound('Warning.mp3')
        op_Move = input("Found move is illegal (error with image recognition or rules) type actual move:")
        time.sleep(3)
        move = chess.Move.from_uci(op_Move)
        board.push(move)

    ####################### MAKE MOVE
    result = engine.play(board, chess.engine.Limit(time=1.0))
    print("1")
    board.push(result.move)
    print("2")
    makeMove(result.move.uci()) #immediately take a photo
    
    print(result.move.uci())
    print(board)

print("GAME FINISHED!")
sys.exit()

# get response
# convert response to move
# play it

#app.top_window().set_focus()



# coordinates on /play/
#1418 346   Start
#985 214    Top Right
#256 212    Top Left
#259 941    Bottom Left
#986 942    Bottom Right

# first move
# 668 814
# 668 620

# versus computer
# 1437 953 start button
# 708 796 pawn 1 move
# 796 623 pawn 2 move

#426 211 Counterclockwise origin top LHS
#1076 212
#1076 861
#428 858

