from typing import Any
import pygame
import math
import random
from threading import Thread

# Dimensions of window
WIDTH: int = 1600
HEIGHT: int = 900

GRAVITY: float = 1
DAMPING: float = 0.999  # Simulates air resistance
ELASTICITY: float = 0.5  # How bouncy the walls are

RADIUS: float = 5
MIN_RADIUS_FACTOR: float = 1  # MIN_RADIUS_FACTOR * RADIUS is the smallest ball
MAX_RADIUS_FACTOR: float = 1  # MAX_RADIUS_FACTOR * RADIUS is the biggest ball

# Desired maximum FPS
FPS: int = 60

NUM_BALLS: int = 2600

INITIAL_VELOCITY_X: float = 6
INITIAL_VELOCITY_Y: float = 0

# Rows and columns of the space partition
# Ensure that HEIGHT / PARTITION_ROWS > RADIUS, WIDTH / PARTITION_COLS > RADIUS so that the ball doesnt belong to multiple cells
PARTITION_ROWS: int = 120
PARTITION_COLS: int = 180

# SHOULD ALWAYS BE > BOUNDARYIES DEFINED BELOW
BALL_START_X: int = WIDTH // 2
BALL_START_Y: int = HEIGHT // 2

# bounding box of balls. NOTE: not fully working since space partitioning does not take this into account, so
# higher values of these will lead to worse performance
LEFT_RIGHT_BOUNDARY: int = WIDTH // 3
UP_DOWN_BOUNDARY: int = HEIGHT // 4

# Number of threads for mulithreading
NUM_THREADS: int = 4
SUBSTEPS: int = 1


class Node:
    def __init__(
        self,
        x: float,
        y: float,
        radius: float,
        color: tuple[int, int, int],
        prev_x: float | None = None,
        prev_y: float | None = None,
    ) -> None:
        self.x: float = x
        self.y: float = y

        self.prev_x = prev_x or x
        self.prev_y = prev_y or y

        self.radius: float = radius
        self.color: tuple[int, int, int] = color

    def draw(self, window: pygame.Surface):
        pygame.draw.circle(window, self.color, (self.x, self.y), self.radius)


class Verlet:
    @classmethod
    def verlet_update(cls, node: Node, dt: float):
        temp: tuple[float, float] = (node.x, node.y)

        accel_x = 0
        accel_y = GRAVITY

        # Apply verlet equation to x and y
        dx = (node.x - node.prev_x) * DAMPING + accel_x * (dt**2)
        dy = (node.y - node.prev_y) * DAMPING + accel_y * (dt**2)

        node.x += dx
        node.y += dy

        node.prev_x, node.prev_y = temp


class CollisionHandler:
    @classmethod
    def distanceBetween(cls, a: Node, b: Node) -> float:
        return math.sqrt(math.pow(a.x - b.x, 2) + math.pow(a.y - b.y, 2))

    @classmethod
    def isColliding(cls, a: Node, b: Node) -> bool:
        return cls.distanceBetween(a, b) < a.radius + b.radius

    @classmethod
    def fixCollision(cls, a: Node, b: Node) -> None:
        distance: float = cls.distanceBetween(a, b)

        # Case where directly over each other
        if distance == 0:
            a.x += 0.1
            b.x -= 0.1
            distance = 0.2

        overlap: float = a.radius + b.radius - distance
        if overlap > 0:
            # Vectors from a -> b. NOTE: The a->b since b - a
            dx: float = b.x - a.x
            dy: float = b.y - a.y

            nx: float = dx / (distance)
            ny: float = dy / (distance)

            # a in negative direction and b in positive direction since vector goes from a -> b
            a.x -= nx * (overlap / 2)
            a.y -= ny * (overlap / 2)

            b.x += nx * (overlap / 2)
            b.y += ny * (overlap / 2)

    @classmethod
    def isOutOfBounds(cls, node: Node) -> bool:
        return (
            node.x - node.radius < 0 + LEFT_RIGHT_BOUNDARY
            or node.x + node.radius > WIDTH - LEFT_RIGHT_BOUNDARY
            or node.y - node.radius < 0 + UP_DOWN_BOUNDARY
            or node.y + node.radius > HEIGHT - UP_DOWN_BOUNDARY
        )

    @classmethod
    def fixBoundary(cls, node: Node) -> None:
        if node.x - node.radius < 0 + LEFT_RIGHT_BOUNDARY:
            node.x = node.radius + LEFT_RIGHT_BOUNDARY
            node.prev_x = node.x + (node.x - node.prev_x) * ELASTICITY
        if node.x + node.radius > WIDTH - LEFT_RIGHT_BOUNDARY:
            node.x = WIDTH - node.radius - LEFT_RIGHT_BOUNDARY
            node.prev_x = node.x + (node.x - node.prev_x) * ELASTICITY
        if node.y - node.radius < 0 + UP_DOWN_BOUNDARY:
            node.y = node.radius + UP_DOWN_BOUNDARY
            node.prev_y = node.y + (node.y - node.prev_y) * ELASTICITY
        if node.y + node.radius > HEIGHT - UP_DOWN_BOUNDARY:
            node.y = HEIGHT - node.radius - UP_DOWN_BOUNDARY
            node.prev_y = node.y + (node.y - node.prev_y) * ELASTICITY


class Util:
    @classmethod
    def getRandomRadius(cls) -> float:
        return RADIUS * random.uniform(MIN_RADIUS_FACTOR, MAX_RADIUS_FACTOR)

    @classmethod
    def getRandomColor(cls) -> tuple[int, int, int]:
        return (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255),
        )

    @classmethod
    def getPartitionFromCoordinates(cls, node: Node):
        # returns (row, column) of partition matrix to which node belongs
        return (
            math.floor(node.y * (PARTITION_ROWS / HEIGHT)),
            math.floor(node.x * (PARTITION_COLS / WIDTH)),
        )

    @classmethod
    def printText(
        cls,
        font: pygame.font.Font,
        text: str,
        window: pygame.Surface,
        location: tuple[int, int],
        color: tuple[int, int, int] = (255, 255, 255),
    ):
        t = font.render(text, True, color)
        window.blit(t, location)

    @classmethod
    def performMultithreadedCollisionHandling(
        cls, partition_matrix: list[list[set[Node]]], startCol: int, endCol: int
    ) -> None:
        for _ in range(SUBSTEPS):
            for row in range(PARTITION_ROWS - 1, -1, -1):
                for col in range(startCol, endCol):
                    for node in partition_matrix[row][col]:
                        for drows in range(-1, 2, 1):
                            if row + drows >= 0 and row + drows < PARTITION_ROWS:
                                for dcols in range(-1, 2, 1):
                                    if (
                                        col + dcols >= 0
                                        and col + dcols < PARTITION_COLS
                                    ):
                                        for otherNode in partition_matrix[row + drows][
                                            col + dcols
                                        ]:
                                            if node is not otherNode:
                                                if CollisionHandler.isColliding(
                                                    node, otherNode
                                                ):
                                                    CollisionHandler.fixCollision(
                                                        node, otherNode
                                                    )
    
    # @classmethod
    # def applyImageToNodes()


if __name__ == "__main__":
    pygame.init()

    window = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2

    font = pygame.font.Font(None, 24)

    running = True
    counter = 0
    nodes_added = 0
    reserved_nodes = [
        Node(
                        BALL_START_X,
                        BALL_START_Y,
                        Util.getRandomRadius(),
                        Util.getRandomColor(),
                        prev_x=BALL_START_X - INITIAL_VELOCITY_X,
                        prev_y=BALL_START_Y + INITIAL_VELOCITY_Y,
        )
        for _ in range(NUM_BALLS)
    ]

    nodes = []
    while running:
        dt = clock.tick(FPS) / 1000  # Convert to seconds

        if nodes_added < NUM_BALLS:
            counter += 1

            if counter == 1:
                # counter = 0
                # nodes.append(
                #     Node(
                #         BALL_START_X,
                #         BALL_START_Y,
                #         Util.getRandomRadius(),
                #         Util.getRandomColor(),
                #         prev_x=BALL_START_X - INITIAL_VELOCITY_X,
                #         prev_y=BALL_START_Y + INITIAL_VELOCITY_Y,
                #     )
                # )  # start node with initial x velocity
                counter = 0
                nodes.append(reserved_nodes[nodes_added])
                nodes_added += 1

        window.fill((0, 0, 0))

        # Update physics
        for node in nodes:
            Verlet.verlet_update(node, dt)
            if CollisionHandler.isOutOfBounds(node):
                CollisionHandler.fixBoundary(node)

        # Create subspace partition matrix
        partition_matrix: list[list[set[Node]]] = []
        for i in range(PARTITION_ROWS):
            temp = []
            for j in range(PARTITION_COLS):
                temp.append(set())
            partition_matrix.append(temp)

        for node in nodes:
            row, col = Util.getPartitionFromCoordinates(node)
            partition_matrix[row][col].add(node)

        # for iteration in range(2):
        evens: Thread | Any = []
        odds: Thread | Any = []

        cols_per_thread = math.ceil(PARTITION_COLS / NUM_THREADS)

        count = 0
        for col in range(0, PARTITION_COLS, cols_per_thread):
            t = Thread(
                target=Util.performMultithreadedCollisionHandling,
                args=(
                    partition_matrix,
                    col,
                    min(PARTITION_COLS, col + cols_per_thread),
                ),
            )
            if count % 2 == 0:
                evens.append(t)
            else:
                odds.append(t)

        for thread in evens:
            thread.start()

        for thread in evens:
            thread.join()

        for thread in odds:
            thread.start()

        for thread in odds:
            thread.join()


        for node in nodes:
            node.draw(window)

        # Print FPS
        Util.printText(font, f"FPS:{str(round(1/dt))}", window, (WIDTH - 100, 25))

        # Print number of balls added so far
        Util.printText(font, f"Balls:{str(len(nodes))}", window, (WIDTH - 100, 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
        # Space stops particles momentarily
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            for node in nodes:
                node.prev_x = node.x
                node.prev_y = node.y



    pygame.quit()