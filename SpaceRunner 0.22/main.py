# flake8:  noqa: E226
from random import random
from random import randint

from cymunk import Body, Circle, Space, Segment, Vec2d
from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window
from kivy.logger import Logger
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.vector import Vector
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.label import Label
from functools import partial

import defs

# __version__ = “1.0.0”

class GameScreenManager(ScreenManager):
    pass

class Planet(Widget):
    pass

class Rock(Widget):
    pass


class KivyGame(Widget):
    #game = None

    def __init__(self, *a, **kwa):
        super().__init__(*a, **kwa)

        self.planets = []
        self.rocks = []
        self.widgets_with_bodies = []
        self.walls = []
        self.space = None
        self.counter = 1   
        self.t = defs.survive_time
        self.check = 1 

        self.app = App.get_running_app()
        Clock.schedule_once(self.init_widgets)

    


    def init_widgets(self, dt):
        w, h = self.size
        
        for _ in range(defs.num_planets):
            planet = Planet(center=(randint(30, w - 30), randint( h, h + 18000)))
            self.planets.append(planet)
            self.add_widget(planet)

        for _ in range(defs.num_rocks):
            rock = Rock(center=(randint(30, w - 30), randint( h, h + 18000)))
            self.rocks.append(rock)
            self.add_widget(rock)

        self.app = App.get_running_app()

        EventLoop.window.bind(on_key_up=self.on_key_up)
        Window.bind(on_resize=self.on_resize)

        self.init_physics()


    def init_physics(self):
        self.space = Space()  # cała fizyka dzieje się w ramach obiektu Space()

        self.init_body(self.ship, defs.ship_collision_type)
        
        for b in self.planets:
            self.init_body(b, defs.planet_collision_type, defs.planet_mass)
            for i in range (1):
                b.body.apply_force((0 , randint(-7600, -1800)))

        for b in self.rocks:
            self.init_body(b, defs.rock_collision_type, defs.rock_mass)
            for i in range (1):
                b.body.apply_force((0 , randint(-150, -50)))

        self.create_walls()

        self.space.add_collision_handler(defs.planet_collision_type,
                                         defs.ship_collision_type,
                                         self.game_lost) #Planeta uderza statek - game over

        self.space.add_collision_handler(defs.rock_collision_type,
                                         defs.ship_collision_type,
                                         self.game_lost) #Skała uderza statek - game over

        self.space.add_collision_handler(defs.default_collision_type,
                                         defs.planet_collision_type,
                                         self.planet_through_wall)#Planeta przelatuje przez krawędź ekranu

        self.space.add_collision_handler(defs.lose_collision_type,
                                         defs.planet_collision_type,
                                         self.planet_through_wall)#Planeta przelatuje przez dolną krawędź ekranu


        self.space.add_collision_handler(defs.default_collision_type,
                                         defs.rock_collision_type,
                                         self.planet_through_wall)#Skała przez krawędź ekranu

        self.space.add_collision_handler(defs.lose_collision_type,
                                         defs.rock_collision_type,
                                         self.planet_through_wall)#Skała przez dolną krawędź ekranu

        self.space.add_collision_handler(defs.planet_collision_type,
                                         defs.rock_collision_type,
                                         self.planet_through_wall)#Skała przeleci przez planetę

    def create_walls(self):
        #Tworzy niewidzialne ściany na krawędziach ekranu
        segments, R = self.wall_segments()
        for (v1, v2), lose in zip(segments, [True, False, False, False]):

            wall = Segment(self.space.static_body, v1, v2, R)
            wall.elasticity = defs.wall_elasticity
            wall.friction = defs.wall_friction
            wall.collision_type = defs.lose_collision_type if lose else defs.default_collision_type

            self.space.add_static(wall)
            self.walls.append(wall)

    def init_body(self, widget, collision_type=defs.default_collision_type, mass = defs.mass, moment = defs.moment):
        """ initialize cymunk body for given widget as circle
            of radius=r
        """
        widget.body = Body(mass, moment)
        widget.body.position = widget.center
        self.widgets_with_bodies.append(widget)

        w, h = widget.size
        r = (w + h) / 4

        shape = Circle(widget.body, r)
        shape.elasticity = defs.elasticity
        shape.friction = defs.friction
        shape.collision_type = collision_type

        self.space.add(widget.body)
        self.space.add(shape)

    def update(self, dt):
        self.space.step(1.0 / 30)

        for w in self.widgets_with_bodies:
            w.center = tuple(w.body.position)

    def on_resize(self, _win, w, h):
        if not self.walls:
            return
        Logger.debug("move walls with width w=%s h=%s", 2*w, 2*h)

        segments, __R = self.wall_segments()

        for (v1, v2), wall in zip(segments,
                                  self.walls):
            wall.a = v1
            wall.b = v2

        self.space.reindex_static()

    def on_key_up(self, __window, key, *__, **___):
        dx, dy = 0, 0
        if key == Keyboard.keycodes['up']:
            dy = 1500
        elif key == Keyboard.keycodes['down']:
            dy = -1500
        elif key == Keyboard.keycodes['left']:
            dx = -1500
        elif key == Keyboard.keycodes['right']:
            dx = +1500

        self.ship.body.apply_impulse(Vector(dx, dy))

    def on_touch_up(self, touch):
        vdir = Vector(touch.pos) - self.ship.center  # wynik to Vector
        self.ship.body.apply_impulse(vdir * 5)


    def my_callback(self, screen, dt):
        if (self.t == 0):
            Clock.unschedule(self.update)
            self.game_won()
        else:
            self.t -= 1
            screen.ids.timer.text = str(self.t)


    def val0(self):
        if (self.check == 1):
            self.check = self.check+1
            Clock.schedule_interval(partial(self.my_callback, self), 1)
        if (self.check == 0):
            Clock.unschedule(partial(self.my_callback, self))
    
    def fix_timer(self, dt):
        self.t+=1

    def start(self):
        if self.counter %2 == 1:
            Clock.schedule_interval(self.update, 1.0 / 30)
            Clock.unschedule(self.fix_timer)
            self.counter += 1
        else:
            Clock.unschedule(self.update)
            Clock.schedule_interval(self.fix_timer, 1)
            self.counter +=1


    def game_lost(self, _space, _arbiter):
        self.counter = 2
        self.start()
        self.app.sm.current = 'lose'

    def game_won(self):
        self.app.sm.current = 'win'


    def planet_through_wall(self, _space, _arbiter):
        return False


    def wall_segments(self):
        w, h = self.size
        R = 200
        return [(Vec2d(-2 * R, -R), Vec2d(w + 2 * R, -R)),
                (Vec2d(-R, -2 * R), Vec2d(-R, h + 2 * R)),
                (Vec2d(-2 * R, h + R), Vec2d(w + 2 * R, h + R)),
                (Vec2d(w + R, h + 2 * R), Vec2d(w + R, -2 * R))], R

class CustomLayout(GridLayout):

    background_image = ObjectProperty(
        Image(
            source='img/background.gif',
            anim_delay=0.03))


class KivyGameApp(App):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        #self.sm = None
    
    def build(self):
        self.sm = GameScreenManager()
        return self.sm

if __name__ == '__main__':
    KivyGameApp().run()
