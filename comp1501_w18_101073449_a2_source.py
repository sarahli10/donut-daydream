# authors: Dr. Robert Collier, Sarah Li
# completed on February 17, 2018

import pygame
import random
import math
import time
import sys

from pygame.locals import *

# initialize mixer for playing background music
pygame.mixer.pre_init(44100, 16, 2, 4096)

pygame.init()  # moved pygame.init() here

# play background music
# souce: https://www.youtube.com/watch?v=YQ1mixa9RAw
pygame.mixer.music.load("bgm.mp3")
pygame.mixer.music.set_volume(0.25) # 0 to 1 scale
pygame.mixer.music.play(-1)  # -1 = loop


# the window is the actual window onto which the camera view is resized and blitted
window_wid = 800
window_hgt = 600

# the frame rate is the number of frames per second that will be displayed and although
# we could (and should) measure the amount of time elapsed, for the sake of simplicity
# we will make the (not unreasonable) assumption that this "delta time" is always 1/fps
frame_rate = 40
delta_time = 1 / frame_rate

# constants for designating the different games states
STATE_TITLE = 0
STATE_READY = 1
STATE_GAME_OVER = 2


# handles the menu selections
def handle_menu_selections(keybd_tupl):
    if keybd_tupl[pygame.K_SPACE]:
        return STATE_READY
    # otherwise the game state will not change
    return STATE_TITLE


# handles the game over selections
def handle_game_over_selections(keybd_tupl, gameData, circle_hitbox):
    if keybd_tupl[pygame.K_SPACE]:
        gameData["score"] = 0
        gameData["health"] = 100
        circle_hitbox["pos"] = [400, 30]

        return STATE_READY
    # otherwise the game state will not change
    else:
        return STATE_GAME_OVER

# rotates the donut
def rotate_sprite(initial_image, position, angle):
    # perform the rotation
    rotated_image = pygame.transform.rotate(initial_image, angle)

    # ensure that the center of the bounding rectangle on the rotated image
    # is at the same position as the center of the rectangle for the initial
    rotated_rect = rotated_image.get_rect(center = position)

    # return the rotated image
    return rotated_image, rotated_rect


# detects if the circle has collided with the donut
def detect_collision_donut_circ(donut_x, donut_y, player_x, player_y):
    donut_rad = 40  # the donuts sprites are 80 x 80 pixels, so the radius of the donut is 40
    player_rad = 20
    # finds the centre of the donut
    donut_centre_x = donut_x + donut_rad
    donut_centre_y = donut_y + donut_rad
    delta_x = abs(player_x - donut_centre_x)
    delta_y = abs(player_y - donut_centre_y)

    if delta_x ** 2 + delta_y ** 2 <= (donut_rad + player_rad) ** 2:
        return True
    return False


# detects if the circle has collided with the line
def detect_collision_line_circ(u, v, gameData):
    # unpack u; a line is an ordered pair of points and a point is an ordered pair of co-ordinates
    (u_sol, u_eol) = u
    (u_sol_x, u_sol_y) = u_sol
    (u_eol_x, u_eol_y) = u_eol

    # unpack v; a circle is a center point and a radius (and a point is still an ordered pair of co-ordinates)
    # ctr = centre
    # rad = radius
    (v_ctr, v_rad) = v
    (v_ctr_x, v_ctr_y) = v_ctr

    # the equation for all points on the line segment u can be considered u = u_sol + t * (u_eol - u_sol), for t in [0, 1]
    # the center of the circle and the nearest point on the line segment (that which we are trying to find) define a line
    # that is is perpendicular to the line segment u (i.e., the dot product will be 0); in other words, it suffices to take

    t = ((v_ctr_x - u_sol_x) * (u_eol_x - u_sol_x) + (v_ctr_y - u_sol_y) * (u_eol_y - u_sol_y)) / (
            (u_eol_x - u_sol_x) ** 2 + (u_eol_y - u_sol_y) ** 2)

    # this t can be used to find the nearest point w on the infinite line between u_sol and u_sol, but the line is not
    # infinite so it is necessary to restrict t to a value in [0, 1]
    t = max(min(t, 1), 0)

    # so the nearest point on the line segment, w, is defined as
    w_x = u_sol_x + t * (u_eol_x - u_sol_x)
    w_y = u_sol_y + t * (u_eol_y - u_sol_y)

    # Euclidean distance squared between w and v_ctr
    d_sqr = (w_x - v_ctr_x) ** 2 + (w_y - v_ctr_y) ** 2

    # if the Eucliean distance squared is less than the radius squared
    if (d_sqr <= v_rad ** 2):
        # the line collides
        gameData["hitLine"] = True
        return True  # the point of collision is (int(w_x), int(w_y))

    else:
        # the line does not collide
        return False


# visit http://ericleong.me/research/circle-line/ for a good supplementary resource on collision detection


def game_loop_inputs():
    # get the state of the keyboard
    keybd_tupl = pygame.key.get_pressed()

    # look in the event queue for the quit event
    quit_ocrd = False

    for evnt in pygame.event.get():
        if evnt.type == QUIT:
            quit_ocrd = True

    # returns the inputs
    return keybd_tupl, quit_ocrd


def game_loop_update(rotating_line, circle_hitbox, gameData, donut):


    gameData["hitLine"] = False
    reached_end = False

    # increase the angle of the rotating line
    rotating_line["ang"] = (rotating_line["ang"] + 0.75)

    # the rotating line angle ranges between 90 and 180 degrees
    if rotating_line["ang"] > 180:
        # when it reaches an angle of 180 degrees, reposition the circular hitbox
        reached_end = True
        rotating_line["ang"] = 90
        gameData["hitLine"] = True
    elif rotating_line["ang"] == 90:
        reached_end = False
        gameData["hitLine"] = False

    # the points associated with each line segment must be recalculated as the angle changes
    rotating_line["seg"] = []

    # consider every line segment length
    for len in rotating_line["len"]:
        # compute the start of the line...
        sol_x = rotating_line["ori"][0] + math.cos(math.radians(rotating_line["ang"])) * window_wid * len[0]
        sol_y = rotating_line["ori"][1] + math.sin(math.radians(rotating_line["ang"])) * window_wid * len[0]

        # ...and the end of the line...
        eol_x = rotating_line["ori"][0] + math.cos(math.radians(rotating_line["ang"])) * window_wid * len[1]
        eol_y = rotating_line["ori"][1] + math.sin(math.radians(rotating_line["ang"])) * window_wid * len[1]

        # ...and then add that line to the list
        rotating_line["seg"].append(((sol_x, sol_y), (eol_x, eol_y)))

    # start by assuming that no collisions have occurred
    circle_hitbox["lineCol"] = False

    # consider possible collisions between the circle hitbox and each line segment
    for seg in rotating_line["seg"]:

        # if there is any collision at all, the circle hitbox flag is set
        if detect_collision_line_circ(seg, (circle_hitbox["pos"], circle_hitbox["rad"]), gameData):
            circle_hitbox["lineCol"] = True
            gameData["hitLine"] = True
            gameData["health"] -= 1
            break

    if detect_collision_donut_circ(donut["pos"][0], donut["pos"][1], circle_hitbox["pos"][0], circle_hitbox["pos"][1]):
        if (gameData["index"] == 4):
            gameData["health"] += 5
        gameData["hitDonut"] = True
        circle_hitbox["donutCol"] = True
        gameData["score"] += 1
        donut["pos"][0] = random.randint(20, window_wid - 100)
        donut["pos"][1] = random.randint(20, window_hgt - 100)

        if (random.randint(0, 10) <= 1):
            gameData["index"] = 4   # donut = rare golden donut
        else:
            gameData["index"] = random.randint(0, 3)


    # return the new state of the rotating line and the circle hitbox
    return rotating_line, circle_hitbox


def game_loop_render(rotating_line, circle_hitbox, window_sfc, gameData, donut, angle):

    # list of colours the line could be
    line_colours = [(255, 86, 86), (252, 141, 68), (255, 251, 40), (176, 252, 0), (48, 255, 55), (0, 255, 165),
                    (30, 210, 255), (108, 142, 252), (153, 108, 252), (255, 89, 210)]
    col = line_colours[random.randint(0, 9)]

    # draw each of the rotating line segments
    for seg in rotating_line["seg"]:
        pygame.draw.aaline(window_sfc, col, seg[0], seg[1])

    # draws a rotating donut on the screen
    rotated, rect = rotate_sprite(donut["image"][gameData["index"]], (donut["pos"][0], donut["pos"][1]), angle)
    rect.center = (donut["pos"][0] + 40, donut["pos"][1] + 40)
    window_sfc.blit(rotated, rect)

    # drawing a circle makes it easier to see the collision between the avatar and the donut
    pygame.draw.circle(window_sfc, (240, 0, 174), circle_hitbox["pos"], circle_hitbox["rad"])

    # draw the circle hitbox, in red if there has been a collision or in white otherwise
    if circle_hitbox["lineCol"]:
        window_sfc.blit(circle_hitbox["image"][4], (circle_hitbox["pos"][0] - 15, circle_hitbox["pos"][1] - 31))

    else:
        window_sfc.blit(circle_hitbox["image"][circle_hitbox["last_key_index"]], (circle_hitbox["pos"][0] - 15, circle_hitbox["pos"][1] - 31))    # original pos = down
        if (circle_hitbox["up"] == True):
            window_sfc.blit(circle_hitbox["image"][0], (circle_hitbox["pos"][0] - 15, circle_hitbox["pos"][1] - 31))
            circle_hitbox["last_key_index"] = 0
            circle_hitbox["up"] = False
        elif (circle_hitbox["down"] == True):
            window_sfc.blit(circle_hitbox["image"][1], (circle_hitbox["pos"][0] - 15, circle_hitbox["pos"][1] - 31))
            circle_hitbox["last_key_index"] = 1
            circle_hitbox["down"] = False
        elif (circle_hitbox["left"] == True):
            window_sfc.blit(circle_hitbox["image"][2], (circle_hitbox["pos"][0] - 15, circle_hitbox["pos"][1] - 31))
            circle_hitbox["last_key_index"] = 2
            circle_hitbox["left"] = False
        elif (circle_hitbox["right"] == True):
            window_sfc.blit(circle_hitbox["image"][3], (circle_hitbox["pos"][0] - 15, circle_hitbox["pos"][1] - 31))
            circle_hitbox["last_key_index"] = 3
            circle_hitbox["right"] = False

    # renders the score
    render_score(gameData, window_sfc)

    # renders the health of the player
    render_health(gameData, window_sfc)

    pygame.display.update()


def render_score(gameData, window_sfc):
    # initialize font
    myfont = pygame.font.SysFont("Century Gothic", 15)

    # render text
    label = myfont.render("Score: %s" % gameData["score"], True, (255, 255, 255))
    window_sfc.blit(label, (30, 30))


def render_health(gameData, window_sfc):
    # initialize font
    myfont = pygame.font.SysFont("Century Gothic", 15)

    # render text
    label = myfont.render("Health: %s" % gameData["health"], True, (255, 255, 255))
    window_sfc.blit(label, (30, 60))



def main():

    # create the window and set the caption of the window
    window_sfc = pygame.display.set_mode((window_wid, window_hgt))
    pygame.display.set_caption("Donut Daydream")

    backgroundFile = pygame.image.load("background.png").convert()
    # window_sfc.blit(backgroundFile, (0, 0))

    # create a clock
    clock = pygame.time.Clock()

    # this is the initial game state
    game_state = STATE_TITLE

    #####################################################################################################
    # these are the initial game objects that are required (in some form) for the core mechanic provided
    #####################################################################################################

    # this game object is a line segment, with a single gap, rotating around a point
    rotating_line_1 = {}
    rotating_line_1["ori"] = [window_wid, 0]  # the "origin" around which the line rotates
    rotating_line_1["ang"] = 135  # the current "angle" of the line, original = 135
    rotating_line_1["len"] = [(0.00, 0.10), (0.20, 0.45), (0.55, 0.75),
                              (0.85, 0.95), (1.05, 1.20)]  # the "length" intervals that specify the gap(s)
    rotating_line_1["seg"] = []  # the individual "segments" (i.e., non-gaps)

    # this game object is a circulr
    circle_hitbox = {}
    circle_hitbox["pos"] = [400, 30]
    circle_hitbox["rad"] = 17
    circle_hitbox["lineCol"] = False  # collision with line
    circle_hitbox["donutCol"] = False  # collision with donut
    circle_hitbox["up"] = False
    circle_hitbox["down"] = False
    circle_hitbox["left"] = False
    circle_hitbox["right"] = False
    circle_hitbox["last_key_index"] = 1 # keeps track of the last key pressed, 0 = up, 1 = down, 2 = left, 3 = right
    circle_hitbox["image"] = []
    circle_hitbox["image"].append(pygame.image.load("avatar up.png").convert_alpha())
    circle_hitbox["image"].append(pygame.image.load("avatar down.png").convert_alpha())
    circle_hitbox["image"].append(pygame.image.load("avatar left.png").convert_alpha())
    circle_hitbox["image"].append(pygame.image.load("avatar right.png").convert_alpha())
    circle_hitbox["image"].append(pygame.image.load("avatar injured.png").convert_alpha())


    # this game object is a donut
    donut = {}
    donut["pos"] = [window_wid / 2, window_hgt / 2]
    donut["image"] = []
    donut["image"].append(pygame.image.load("chocolate.png").convert_alpha())
    donut["image"].append(pygame.image.load("mint.png").convert_alpha())
    donut["image"].append(pygame.image.load("strawberry.png").convert_alpha())
    donut["image"].append(pygame.image.load("vanilla.png").convert_alpha())
    donut["image"].append(pygame.image.load("golden.png").convert_alpha())

    gameData = {"score": 0,
                "health": 100,
                "hitLine": False,
                "hitDonut": False,
                "index": 0}             # donut index

    angle = 0

    # the game loop is a postcondition loop controlled using a Boolean flag
    closed_flag = False

    while not closed_flag:

        #####################################################################################################
        # this is the "inputs" phase of the game loop, where player input is retrieved and stored
        #####################################################################################################

        keybd_tupl, closed_flag = game_loop_inputs()

        x_pos = circle_hitbox["pos"][0]
        y_pos = circle_hitbox["pos"][1]

        # the circle moves when the player presses up, down, left, or right
        rate = 7
        if keybd_tupl[pygame.K_UP]:
            if not (y_pos - rate < 0):
                circle_hitbox["up"] = True
                circle_hitbox["pos"][1] -= rate
        elif keybd_tupl[pygame.K_DOWN]:
            if not (y_pos + rate > window_hgt):
                circle_hitbox["down"] = True
                circle_hitbox["pos"][1] += rate
        elif keybd_tupl[pygame.K_LEFT]:
            if not (x_pos - rate < 0):
                circle_hitbox["left"] = True
                circle_hitbox["pos"][0] -= rate
        elif keybd_tupl[pygame.K_RIGHT]:
            if not (x_pos + rate > window_wid):
                circle_hitbox["right"] = True
                circle_hitbox["pos"][0] += rate

        #####################################################################################################
        # this is the "update" phase of the game loop, where the changes to the game world are handled
        #####################################################################################################

        if game_state == STATE_TITLE:
            next_state = handle_menu_selections(keybd_tupl)

        elif game_state == STATE_READY:
            rotating_line_1, circle_hitbox = game_loop_update(rotating_line_1, circle_hitbox, gameData, donut)


        elif game_state == STATE_GAME_OVER:
            next_state = handle_game_over_selections(keybd_tupl, gameData, circle_hitbox)

        #####################################################################################################
        # this is the "render" phase of the game loop, where a representation of the game world is displayed
        #####################################################################################################

        if game_state == STATE_TITLE:
            title_img = pygame.image.load("title.png").convert()
            window_sfc.blit(pygame.transform.smoothscale(title_img, (window_wid, window_hgt)),
                            (0, 0))
            pygame.display.update()

        elif game_state == STATE_READY:
            window_sfc.blit(backgroundFile, (0, 0))

            angle += 1
            game_loop_render(rotating_line_1, circle_hitbox, window_sfc, gameData, donut, angle)

            if game_state == STATE_TITLE:
                next_state = handle_menu_selections(keybd_tupl)

            if gameData["health"] == 0:
                next_state = STATE_GAME_OVER

        elif game_state == STATE_GAME_OVER:
            game_over_img = pygame.image.load("game over.png").convert()
            window_sfc.blit(pygame.transform.smoothscale(game_over_img, (window_wid, window_hgt)),
                            (0, 0))

            myfont = pygame.font.SysFont("Century Gothic", 30)
            label = myfont.render("You ate %s donuts!" % gameData["score"], True, (241, 204, 255))
            window_sfc.blit(label, (148, 400))

            pygame.display.update()

        game_state = next_state

        # enforce the minimum frame rate
        clock.tick(frame_rate)


if __name__ == "__main__":
    main()
