import pygame
import sys
import random
from pytmx.util_pygame import load_pygame

pygame.init()
pygame.mixer.init()
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
pantalla_completa = True
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.SCALED | pygame.FULLSCREEN
)
pygame.display.set_caption("Viernes 13: El Pixel Muerto")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
FONT = pygame.font.Font(None, 36)
TITLE_FONT = pygame.font.Font(None, 72)
PANTALLA_LOGO = 1
PANTALLA_MENU = 2
PANTALLA_CONTROLES = 3
PANTALLA_CREDITOS = 4
PANTALLA_JUEGO = 5
PANTALLA_MUNDO = 6
PANTALLA_CASA = 7
PANTALLA_CASA_JASON = 8
PANTALLA_GAME_OVER = 9
PANTALLA_PAUSA = 10
estado_actual = PANTALLA_LOGO
estado_anterior_pausa = PANTALLA_MUNDO
pantalla_pausa_fondo = None
logo_timer = 1250
logo_image = pygame.image.load("assets/logo.png").convert_alpha()
logo_image = pygame.transform.scale(logo_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
velocitat_animacio = 200
musica_menu_reproduciendo = False
tiempo_total = 15 * 60 * 1000
tiempo_restante = tiempo_total
tiempo_iniciado = False
mostrar_coordenadas = False
DISTANCIA_DETECCION = 80 #Distancia a la que el jugador puede atacar a los campistas
DISTANCIA_HUIDA = 300 #Distancia a la que los campistas comienzan a huir del jugador
colisiones_mundo = [
    pygame.Rect(0, 0, 340, 340),
    pygame.Rect(750, 0, 200, 150),
    pygame.Rect(745, 610, 150, 60),
    pygame.Rect(100, 870, 150, 60),
    pygame.Rect(940, 1150, 150, 60),
    pygame.Rect(1320, 810, 150, 60),
    pygame.Rect(1645, 1200, 150, 60),
]
mostrar_colisiones = False
mostrar_hitboxes = False
def cambiar_modo_pantalla():
    global screen, pantalla_completa
    pantalla_completa = not pantalla_completa
    flags = pygame.SCALED
    if pantalla_completa:
        flags |= pygame.FULLSCREEN
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
class TiledMap:
    def __init__(self, filename):
        self.tmx_data = load_pygame(filename)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight
        self.map_surface = pygame.Surface((self.width, self.height))
    def render(self, surface):
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        surface.blit(tile, (x * self.tmx_data.tilewidth,
                                            y * self.tmx_data.tileheight))
    def make_map(self):
        self.render(self.map_surface)
        return self.map_surface
    def get_tile_properties(self, x, y, layer):
        try:
            return self.tmx_data.get_tile_properties(x, y, layer)
        except:
            return None
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)
    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)
    def update(self, target):
        if self.width <= SCREEN_WIDTH:
            x = (SCREEN_WIDTH - self.width) // 2
        else:
            x = -target.rect.centerx + SCREEN_WIDTH // 2
            x = min(0, x)
            x = max(SCREEN_WIDTH - self.width, x)

        if self.height <= SCREEN_HEIGHT:
            y = (SCREEN_HEIGHT - self.height) // 2
        else:
            y = -target.rect.centery + SCREEN_HEIGHT // 2
            y = min(0, y)
            y = max(SCREEN_HEIGHT - self.height, y)

        self.camera = pygame.Rect(x, y, self.width, self.height)
def dibujar_mapa_escalado(surface, mapa, entidad):
    """Dibuja un mapa pequeño ampliado sin deformar sus proporciones."""
    escala = min(SCREEN_WIDTH / mapa.width, SCREEN_HEIGHT / mapa.height)
    ancho = round(mapa.width * escala)
    alto = round(mapa.height * escala)
    x = (SCREEN_WIDTH - ancho) // 2
    y = (SCREEN_HEIGHT - alto) // 2
    mapa_escalado = pygame.transform.scale(surface, (ancho, alto))
    screen.blit(mapa_escalado, (x, y))
    imagen_ancho = max(1, round(entidad.image.get_width() * escala))
    imagen_alto = max(1, round(entidad.image.get_height() * escala))
    imagen_escalada = pygame.transform.scale(
        entidad.image, (imagen_ancho, imagen_alto)
    )
    posicion = (
        x + round(entidad.rect.x * escala),
        y + round(entidad.rect.y * escala)
    )
    screen.blit(imagen_escalada, posicion)
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = None
        self.rect = None
        self.directions = ['down', 'up', 'left', 'right']
        self.current_direction = 'down'
        self.sprites = self.load_sprites()
        self.current_frame = 0
        self.animation_speed = velocitat_animacio
        self.last_update_time = pygame.time.get_ticks()
        self.image = self.sprites[self.current_direction][0]
        self.rect = self.image.get_rect(topleft=(1400, 700))
    def cambiar_sprites(self, carpeta):
        self.sprites = {}
        for direction in self.directions:
            self.sprites[direction] = [
                pygame.image.load(f"{carpeta}/jugador-{direction}-{i}.png").convert_alpha()
                for i in range(3)
            ]
        self.image = self.sprites[self.current_direction][0]
    def load_sprites(self):
        sprites = {}
        for direction in self.directions:
            sprites[direction] = [
                pygame.image.load(f"assets/personaje1/jugador-{direction}-{i}.png").convert_alpha()
                for i in range(3)
            ]
        return sprites
    def update(self, keys, map_width=None, map_height=None, colisiones=None):
        speed = 5
        moving = False
        direction_changed = False
        new_x = self.rect.x
        new_y = self.rect.y
        if keys[pygame.K_a]:
            new_x -= speed
            self.current_direction = 'left'
            moving = True
            direction_changed = True
        if keys[pygame.K_d]:
            new_x += speed
            self.current_direction = 'right'
            moving = True
            direction_changed = True
        if keys[pygame.K_w]:
            new_y -= speed
            if not direction_changed:
                self.current_direction = 'up'
            moving = True
        if keys[pygame.K_s]:
            new_y += speed
            if not direction_changed:
                self.current_direction = 'down'
            moving = True
        temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
        if colisiones:
            collision_detected = False
            for colision in colisiones:
                if temp_rect.colliderect(colision):
                    collision_detected = True
                    break

            if collision_detected:
                pass
            else:
                if map_width is not None and map_height is not None:
                    if 0 <= new_x <= map_width - self.rect.width:
                        self.rect.x = new_x
                    if 0 <= new_y <= map_height - self.rect.height:
                        self.rect.y = new_y
                else:
                    self.rect.x = new_x
                    self.rect.y = new_y
        else:
            if map_width is not None and map_height is not None:
                if 0 <= new_x <= map_width - self.rect.width:
                    self.rect.x = new_x
                if 0 <= new_y <= map_height - self.rect.height:
                    self.rect.y = new_y
            else:
                self.rect.x = new_x
                self.rect.y = new_y
        self.animate(moving)
    def animate(self, moving):
        current_time = pygame.time.get_ticks()
        if moving:
            if current_time - self.last_update_time > self.animation_speed:
                self.current_frame = 1 if self.current_frame == 2 else 2
                self.last_update_time = current_time
        else:
            self.current_frame = 0
        self.image = self.sprites[self.current_direction][self.current_frame]
class Campista(pygame.sprite.Sprite):
    def __init__(self, id_campista, pos_x, pos_y, map_width, map_height):
        super().__init__()
        self.id_campista = id_campista % 5 + 1
        self.x = pos_x
        self.y = pos_y
        self.velocidad = 2
        self.velocidad_huida = 3
        self.directions = ['down', 'up', 'left', 'right']
        self.current_direction = random.choice(self.directions)
        self.tiempo_cambio_direccion = random.randint(1000, 3000)
        self.ultimo_cambio = pygame.time.get_ticks()
        self.current_frame = 0
        self.animation_speed = velocitat_animacio
        self.last_update_time = pygame.time.get_ticks()
        self.sprites = self.load_sprites()
        self.image = self.sprites[self.current_direction][0]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.map_width = map_width
        self.map_height = map_height
        self.huyendo = False
        self.vivo = True
    def load_sprites(self):
        sprites = {}
        for direction in self.directions:
            sprites[direction] = []
            try:
                for frame in range(3):
                    path = f"assets/campistas/campista{self.id_campista}/campista_{self.id_campista}-{direction}-{frame}.png"
                    sprite = pygame.image.load(path).convert_alpha()
                    sprite = pygame.transform.scale(sprite, (sprite.get_width() * 2, sprite.get_height() * 2))
                    sprites[direction].append(sprite)
            except pygame.error as e:
                print(f"Error al cargar sprite de campista {self.id_campista}: {e}")
        return sprites
    def update(self, player=None, colisiones=None):
        if not self.vivo:
            return
        if player:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance < DISTANCIA_HUIDA:
                self.huyendo = True
                if abs(dx) > abs(dy):
                    if dx > 0:
                        self.current_direction = 'left'
                    else:
                        self.current_direction = 'right'
                else:
                    if dy > 0:
                        self.current_direction = 'up'
                    else:
                        self.current_direction = 'down'
                self.ultimo_cambio = pygame.time.get_ticks()
            else:
                self.huyendo = False
                self.cambiar_direccion()
        else:
            self.huyendo = False
            self.cambiar_direccion()
        self.mover(colisiones)
        self.animar()
    def cambiar_direccion(self):
        now = pygame.time.get_ticks()
        if now - self.ultimo_cambio > self.tiempo_cambio_direccion:
            self.current_direction = random.choice(self.directions)
            self.tiempo_cambio_direccion = random.randint(1000, 3000)
            self.ultimo_cambio = now
    def mover(self, colisiones=None):
        velocidad_actual = self.velocidad_huida if self.huyendo else self.velocidad
        nueva_x, nueva_y = self.x, self.y
        if self.current_direction == 'up':
            nueva_y -= velocidad_actual
        elif self.current_direction == 'down':
            nueva_y += velocidad_actual
        elif self.current_direction == 'left':
            nueva_x -= velocidad_actual
        elif self.current_direction == 'right':
            nueva_x += velocidad_actual
        temp_rect = pygame.Rect(nueva_x, nueva_y, self.rect.width, self.rect.height)
        collision_detected = False
        if colisiones:
            for colision in colisiones:
                if temp_rect.colliderect(colision):
                    collision_detected = True
                    break
        if not collision_detected and (0 <= nueva_x <= self.map_width - self.rect.width and
                                       0 <= nueva_y <= self.map_height - self.rect.height):
            self.x, self.y = nueva_x, nueva_y
        else:
            self.current_direction = random.choice(self.directions)
            self.ultimo_cambio = pygame.time.get_ticks()
        self.rect.topleft = (self.x, self.y)
    def animar(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time > self.animation_speed:
            self.current_frame = 1 if self.current_frame == 2 else 2
            self.last_update_time = current_time
        self.image = self.sprites[self.current_direction][self.current_frame]
class BarraPrecision:
    def __init__(self, screen_width, screen_height):
        self.width = 300
        self.height = 30
        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height // 2 - self.height // 2
        self.target_width = 40
        self.marker_pos = 0
        self.marker_speed = 5
        self.marker_direction = 1
        self.active = False
        self.start_time = 0
        self.time_limit = 3000
        self.target_pos = random.randint(50, self.width - self.target_width - 50)
    def start(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()
        self.marker_pos = 0
        self.marker_direction = 1
        self.target_pos = random.randint(50, self.width - self.target_width - 50)
    def update(self):
        if not self.active:
            return False, False
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time > self.time_limit:
            self.active = False
            return False, True
        self.marker_pos += self.marker_speed * self.marker_direction
        if self.marker_pos <= 0 or self.marker_pos >= self.width:
            self.marker_direction *= -1
        return False, False
    def draw(self, screen):
        if not self.active:
            return
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        pygame.draw.rect(screen, (0, 255, 0), (self.x + self.target_pos, self.y, self.target_width, self.height))
        pygame.draw.rect(screen, RED, (self.x + self.marker_pos, self.y - 10, 5, self.height + 20))
        tiempo_restante = max(0, self.time_limit - (pygame.time.get_ticks() - self.start_time)) // 1000 + 1
        tiempo_text = FONT.render(f"Tiempo: {tiempo_restante}", True, RED)
        screen.blit(tiempo_text, (self.x + self.width // 2 - tiempo_text.get_width() // 2, self.y - 40))
    def check_hit(self):
        if not self.active:
            return False
        if self.target_pos <= self.marker_pos <= self.target_pos + self.target_width:
            self.active = False
            return True
        else:
            return False
barra_precision = BarraPrecision(SCREEN_WIDTH, SCREEN_HEIGHT)
try:
    casa_map = TiledMap("assets/mapas/casa_jason.tmx")
except Exception as e:
    print(f"Error al cargar casa_map: {e}")
    casa_map = None
try:
    mundo_map = TiledMap("assets/mapas/mundo.tmx")
except Exception as e:
    print(f"Error al cargar mundo_map: {e}")
    mundo_map = None
try:
    casa_jason_map = TiledMap("assets/mapas/casa_jason.tmx")
except Exception as e:
    print(f"Error al cargar casa_jason_map: {e}")
    casa_jason_map = None
try:
    gameover_image = pygame.image.load("assets/gameover.png").convert_alpha()
    gameover_image = pygame.transform.scale(gameover_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception as e:
    print(f"Error al cargar gameover_image: {e}")
    gameover_image = None
player = Player()
all_sprites = pygame.sprite.Group(player)
campistas = pygame.sprite.Group()
def crear_campistas(num_campistas=20):
    for campista in campistas:
        all_sprites.remove(campista)
    campistas.empty()
    if mundo_map:
        map_width = mundo_map.width
        map_height = mundo_map.height
        for i in range(1, num_campistas + 1):
            posicion_valida = False
            intentos = 0
            max_intentos = 100 
            while not posicion_valida and intentos < max_intentos:
                intentos += 1
                pos_x = random.randint(100, map_width - 100)
                pos_y = random.randint(100, map_height - 100)
                enemigo = Campista(i, pos_x, pos_y, map_width, map_height)
                colisiona = False
                for colision in colisiones_mundo:
                    if enemigo.rect.colliderect(colision):
                        colisiona = True
                        break
                if not colisiona:
                    posicion_valida = True
                    campistas.add(enemigo)
                    all_sprites.add(enemigo)
def iniciar_partida():
    global current_map, current_camera, tiempo_iniciado, tiempo_restante
    crear_campistas()
    tiempo_iniciado = False
    tiempo_restante = tiempo_total
    current_map = casa_jason_map
    current_camera = casa_jason_camera
    player.cambiar_sprites("assets/personaje1")
    player.rect.center = (casa_jason_map.width // 2, casa_jason_map.height // 2)
casa_camera = None
mundo_camera = None
casa_jason_camera = Non
try:
    casa_camera = Camera(casa_map.width, casa_map.height)
    mundo_camera = Camera(mundo_map.width, mundo_map.height)
    casa_jason_camera = Camera(casa_jason_map.width, casa_jason_map.height)
except:
    pass
current_camera = None
current_map = None
def format_time(millis):
    seconds = millis // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"
def campista_cerca():
    campista_cercano = None
    menor_distancia = DISTANCIA_DETECCION
    for campista in campistas:
        if not campista.vivo:
            continue
        dx = player.rect.centerx - campista.rect.centerx
        dy = player.rect.centery - campista.rect.centery
        distancia = (dx ** 2 + dy ** 2) ** 0.5
        if distancia < menor_distancia:
            menor_distancia = distancia
            campista_cercano = campista
    return campista_cercano
clock = pygame.time.Clock()
running = True
while running:
    screen.fill(BLACK)
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            cambiar_modo_pantalla()
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and
                estado_actual in (PANTALLA_MUNDO, PANTALLA_CASA_JASON)):
            pantalla_pausa_fondo = screen.copy()
            estado_anterior_pausa = estado_actual
            estado_actual = PANTALLA_PAUSA
        if event.type == pygame.KEYDOWN and estado_actual == PANTALLA_PAUSA:
            if event.key == pygame.K_r:
                estado_actual = estado_anterior_pausa
                pantalla_pausa_fondo = None
            elif event.key == pygame.K_q:
                running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            mostrar_coordenadas = not mostrar_coordenadas
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            mostrar_colisiones = not mostrar_colisiones
        if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
            mostrar_hitboxes = not mostrar_hitboxes
        if event.type == pygame.KEYDOWN and event.key == pygame.K_k and estado_actual == PANTALLA_MUNDO:
            campista_objetivo = campista_cerca()
            if campista_objetivo and not barra_precision.active:
                barra_precision.start()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and barra_precision.active:
            if barra_precision.check_hit():
                campista_objetivo = campista_cerca()
                if campista_objetivo:
                    campista_objetivo.vivo = False
                    all_sprites.remove(campista_objetivo)
                    campistas.remove(campista_objetivo)
            else:
                barra_precision.active = False
    if barra_precision.active:
        exito, tiempo_agotado = barra_precision.update()
        if tiempo_agotado:
            barra_precision.active = False
    #Pantalla 1
    if estado_actual == PANTALLA_LOGO:
        screen.blit(logo_image, (0, 0))
        pygame.time.delay(100)
        logo_timer -= clock.get_time()
        if logo_timer <= 0:
            estado_actual = PANTALLA_MENU
    #Pantalla 2
    elif estado_actual == PANTALLA_MENU:
        if estado_actual == PANTALLA_MENU and not musica_menu_reproduciendo:
            pygame.mixer.music.load("assets/audio/menu_music.mp3")
            pygame.mixer.music.set_volume(0.1)  # Opcional: volumen entre 0.0 y 1.0
            pygame.mixer.music.play(-1)  # -1 para que se repita en bucle
            musica_menu_reproduciendo = True
        title_render = TITLE_FONT.render("El Pixel Muerto", True, RED)
        title_x = SCREEN_WIDTH // 2 - title_render.get_width() // 2
        screen.blit(title_render, (title_x, 100))
        menu_text = [
            "1. Ir al juego",
            "2. Controles",
            "3. Créditos",
            "ESC: Salir"
        ]
        y = 200
        for text in menu_text:
            render = FONT.render(text, True, WHITE)
            x = SCREEN_WIDTH // 2 - render.get_width() // 2
            screen.blit(render, (x, y))
            y += 50
        if keys[pygame.K_1]:
            estado_actual = PANTALLA_CASA_JASON
            iniciar_partida()
        elif keys[pygame.K_2]:
            estado_actual = PANTALLA_CONTROLES
        elif keys[pygame.K_3]:
            estado_actual = PANTALLA_CREDITOS
        elif keys[pygame.K_ESCAPE]:
            running = False
    #Pantalla 3
    elif estado_actual == PANTALLA_CONTROLES:
        controls_text = [
            "Controles del juego:",
            "",
            "Teclas de movimiento",
            "W: Mover hacia arriba",
            "A: Mover a la izquierda",
            "S: Mover hacia abajo",
            "D: Mover a la derecha",
            "K: Matar campista (cuando estés cerca)",
            "F: Cambiar modo de pantalla",
            "P: Mostrar/Ocultar coordenadas",
            "C: Mostrar/Ocultar colisiones (depuración)",
            "O: Mostrar/Ocultar hitboxes (depuración)",
            "Presiona 'ENTER' para regresar al menú"
        ]
        y = 120
        for text in controls_text:
            render = FONT.render(text, True, WHITE)
            x = SCREEN_WIDTH // 2 - render.get_width() // 2
            screen.blit(render, (x, y))
            y += 50
        if event.type == pygame.KEYDOWN:
            estado_actual = PANTALLA_MENU
    #Pantalla 4
    elif estado_actual == PANTALLA_CREDITOS:
        rules_text = [
            "Créditos:",
            "",
            "Gráficos: Dídac Perales Cuadros",
            "Código: Christian Massa Aiassa (También Xavi sancho)",
            "Musica Menú: Doom",
            "Sonidos en próximas actualizaciones"
            ]
        y = 150
        for text in rules_text:
            render = FONT.render(text, True, WHITE)
            x = SCREEN_WIDTH // 2 - render.get_width() // 2
            screen.blit(render, (x, y))
            y += 50
        if event.type == pygame.KEYDOWN:
            estado_actual = PANTALLA_MENU
    #Pantalla 5
    if (estado_actual not in (PANTALLA_MENU, PANTALLA_PAUSA) and
            musica_menu_reproduciendo):
        pygame.mixer.music.stop()
        musica_menu_reproduciendo = False
    elif estado_actual == PANTALLA_JUEGO:
        if current_map:
            player.update(keys, current_map.width, current_map.height)
            if current_camera:
                current_camera.update(player)
                map_surface = current_map.make_map()
                screen.blit(map_surface, current_camera.camera.topleft)
                screen.blit(player.image, current_camera.apply(player))
                if current_map == casa_map and player.rect.top <= 50:
                    estado_actual = PANTALLA_MUNDO
                    current_map = mundo_map
                    current_camera = mundo_camera
                    player.rect.centerx = mundo_map.width // 2
                    player.rect.bottom = mundo_map.height - 100
                    crear_campistas(20)
                    tiempo_iniciado = True
                    tiempo_restante = tiempo_total
                if mostrar_coordenadas:
                    coords_text = FONT.render(f"X: {player.rect.x}, Y: {player.rect.y}", True, RED)
                    screen.blit(coords_text, (20, 60))
    #Menú de pausa
    elif estado_actual == PANTALLA_PAUSA:
        if pantalla_pausa_fondo:
            screen.blit(pantalla_pausa_fondo, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))
        pausa_texto = TITLE_FONT.render("PAUSA", True, WHITE)
        pausa_x = SCREEN_WIDTH // 2 - pausa_texto.get_width() // 2
        screen.blit(pausa_texto, (pausa_x, SCREEN_HEIGHT // 2 - 130))
        reanudar_texto = FONT.render("R: Reanudar", True, WHITE)
        cerrar_texto = FONT.render("Q: Cerrar juego", True, WHITE)
        screen.blit(
            reanudar_texto,
            (SCREEN_WIDTH // 2 - reanudar_texto.get_width() // 2,
             SCREEN_HEIGHT // 2 - 20)
        )
        screen.blit(
            cerrar_texto,
            (SCREEN_WIDTH // 2 - cerrar_texto.get_width() // 2,
             SCREEN_HEIGHT // 2 + 30)
        )
    # Pantalla 6
    elif estado_actual == PANTALLA_MUNDO:
        if mundo_map and mundo_camera:
            if current_map != mundo_map:
                current_map = mundo_map
                current_camera = mundo_camera
                
                colisiones_mundo.clear()
            if tiempo_iniciado:
                tiempo_restante -= clock.get_time()
                if tiempo_restante <= 0:
                    estado_actual = PANTALLA_GAME_OVER
            player.cambiar_sprites("assets/personaje2")
            player.update(keys, mundo_map.width, mundo_map.height, colisiones_mundo)
            for campista in campistas:
                campista.update(player, colisiones_mundo)
            mundo_camera.update(player)
            map_surface = mundo_map.make_map()
            screen.blit(map_surface, mundo_camera.camera.topleft)
            # Dibujar colisiones si está activado
            if mostrar_colisiones:
                for colision in colisiones_mundo:
                    colision_en_pantalla = mundo_camera.apply_rect(colision)
                    pygame.draw.rect(screen, (255, 0, 0), colision_en_pantalla, 2)
            if mostrar_hitboxes:
                # Hitbox del jugador (Verde)
                pygame.draw.rect(screen, (0, 255, 0), mundo_camera.apply(player), 2)
                # Hitboxes de los campistas (Amarillo)
                for campista in campistas:
                    if campista.vivo:
                        pygame.draw.rect(screen, (255, 255, 0), mundo_camera.apply(campista), 2)
            for entity in all_sprites:
                if entity in campistas and not entity.vivo:
                    continue
                screen.blit(entity.image, mundo_camera.apply(entity))
            tiempo_texto = format_time(tiempo_restante)
            tiempo_render = FONT.render(f"Tiempo: {tiempo_texto}", True, RED)
            screen.blit(tiempo_render, (20, 20))
            # Mostrar coordenadas del jugador si está activado
            if mostrar_coordenadas:
                coords_text = FONT.render(f"X: {player.rect.x}, Y: {player.rect.y}", True, RED)
                screen.blit(coords_text, (20, 60))
            campista_objetivo = campista_cerca()
            if campista_objetivo:
                matar_texto = FONT.render("'K' para MATAR", True, RED)
                texto_x = campista_objetivo.rect.centerx - matar_texto.get_width() // 2
                texto_y = campista_objetivo.rect.top - 30
                pos_texto = mundo_camera.apply_rect(pygame.Rect(texto_x, texto_y, 0, 0))
                screen.blit(matar_texto, pos_texto)
            casa_jason_entrada = pygame.Rect(mundo_map.width // 2, mundo_map.height // 3, 50, 50)
            if casa_jason_entrada.colliderect(player.rect) and keys[pygame.K_e]:
                estado_actual = PANTALLA_CASA_JASON
                current_map = casa_jason_map
                current_camera = casa_jason_camera
                player.rect.center = (casa_jason_map.width // 2, casa_jason_map.height - 200)
            if tiempo_iniciado and len(campistas) == 0:
                victoria_texto = TITLE_FONT.render("¡VICTORIA!", True, RED)
                x = SCREEN_WIDTH // 2 - victoria_texto.get_width() // 2
                screen.blit(victoria_texto, (x, SCREEN_HEIGHT // 2))
                pygame.display.flip()
                pygame.time.delay(3000)
                estado_actual = PANTALLA_MENU
        else:
            if keys[pygame.K_RETURN]:
                estado_actual = PANTALLA_CASA
    # Pantalla 7
    elif estado_actual == PANTALLA_CASA:
        screen.fill(GRAY)
        text = FONT.render("Casa: Presiona cualquier tecla para salir.", True, WHITE)
        x = SCREEN_WIDTH // 2 - text.get_width() // 2
        screen.blit(text, (x, SCREEN_HEIGHT // 2))

        # Mostrar coordenadas del jugador si está activado
        if mostrar_coordenadas:
            coords_text = FONT.render(f"X: {player.rect.x}, Y: {player.rect.y}", True, WHITE)
            screen.blit(coords_text, (20, 60))

        if event.type == pygame.KEYDOWN:
            estado_actual = PANTALLA_MUNDO
    # Pantalla 8
    elif estado_actual == PANTALLA_CASA_JASON:
        if casa_jason_map and casa_jason_camera:
            player.update(keys, casa_jason_map.width, casa_jason_map.height)
            casa_jason_camera.update(player)
            map_surface = casa_jason_map.make_map()
            dibujar_mapa_escalado(map_surface, casa_jason_map, player)
            if tiempo_iniciado:
                tiempo_restante -= clock.get_time()
                if tiempo_restante <= 0:
                    estado_actual = PANTALLA_GAME_OVER

                tiempo_texto = format_time(tiempo_restante)
                tiempo_render = FONT.render(f"Tiempo: {tiempo_texto}", True, RED)
                screen.blit(tiempo_render, (20, 20))
            if mostrar_coordenadas:
                coords_text = FONT.render(f"X: {player.rect.x}, Y: {player.rect.y}", True, RED)
                screen.blit(coords_text, (20, 60))
            salida_texto = FONT.render("Pulsa E para salir de la casa", True, WHITE)
            screen.blit(
                salida_texto,
                (SCREEN_WIDTH // 2 - salida_texto.get_width() // 2, SCREEN_HEIGHT - 50)
            )
            if keys[pygame.K_e]:
                estado_actual = PANTALLA_MUNDO
                current_map = mundo_map
                current_camera = mundo_camera
                player.rect.center = (mundo_map.width // 2, mundo_map.height // 3 + 100)
                if not tiempo_iniciado:
                    crear_campistas()
                    tiempo_iniciado = True
                    tiempo_restante = tiempo_total
        else:
            if event.type == pygame.KEYDOWN:
                estado_actual = PANTALLA_MUNDO
    # Pantalla 9: Game Over
    elif estado_actual == PANTALLA_GAME_OVER:
        if gameover_image:
            screen.blit(gameover_image, (0, 0))
        else:
            screen.fill(BLACK)
            gameover_text = TITLE_FONT.render("GAME OVER", True, RED)
            x = SCREEN_WIDTH // 2 - gameover_text.get_width() // 2
            screen.blit(gameover_text, (x, SCREEN_HEIGHT // 2 - 50))

            restart_text = FONT.render("Presiona ESPACIO para volver al menú", True, WHITE)
            x = SCREEN_WIDTH // 2 - restart_text.get_width() // 2
            screen.blit(restart_text, (x, SCREEN_HEIGHT // 2 + 50))
        if keys[pygame.K_SPACE]:
            estado_actual = PANTALLA_MENU
            tiempo_iniciado = False
            tiempo_restante = tiempo_total
    if barra_precision.active:
        barra_precision.draw(screen)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
sys.exit()
