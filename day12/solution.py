import argparse
import re
from copy import deepcopy
from itertools import combinations
from math import gcd
from typing import List

INPUT_REGEXP = re.compile(r'^<x=(-?[0-9]+),[ ]*y=(-?[0-9]+),[ ]*z=(-?[0-9]+)>$')


def lcm(a: int, b: int) -> int:
    """Find least common multiple of 2 integers"""
    return a * b // gcd(a, b)


class Coordinates:
    def __init__(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self) -> str:
        return f'<x={self.x:3d},y={self.y:3d},z={self.z:3d}>'


class Gravity(Coordinates):
    def __repr__(self) -> str:
        return f'grv:{super().__repr__()}'


class Velocity(Coordinates):
    def __repr__(self) -> str:
        return f'vel:{super().__repr__()}'

    def accelerate(self, gravity: Gravity) -> None:
        self.x += gravity.x
        self.y += gravity.y
        self.z += gravity.z


class Position(Coordinates):
    def __repr__(self) -> str:
        return f'pos:{super().__repr__()}'

    def move(self, velocity: Velocity) -> None:
        self.x += velocity.x
        self.y += velocity.y
        self.z += velocity.z


class Star:
    def __init__(self, position: Position, velocity: Velocity) -> None:
        self.position = position
        self.velocity = velocity
        self.gravity = Gravity()

    def __repr__(self) -> str:
        return f'{self.position.__repr__()}, {self.velocity.__repr__()}'

    def updateGForceForPair(self, other: 'Star') -> None:
        """
        Compares this star's position with another's, compute gravitational
        effects on one another and add to the total gravity for both stars.
        """
        def compareIndividualDimension(dimension: str) -> None:
            if self.position.__dict__[dimension] > other.position.__dict__[dimension]:
                self.gravity.__dict__[dimension] -= 1
                other.gravity.__dict__[dimension] += 1
            elif self.position.__dict__[dimension] < other.position.__dict__[dimension]:
                self.gravity.__dict__[dimension] += 1
                other.gravity.__dict__[dimension] -= 1

        for dimension in ['x', 'y', 'z']:
            compareIndividualDimension(dimension)

    def updateVelocity(self) -> None:
        """Update star's velocity based on current gravity."""
        self.velocity.accelerate(self.gravity)

    def updatePosition(self) -> None:
        """Update star's position based on current velocity."""
        self.position.move(self.velocity)

    def energy(self) -> int:
        """Get star's total energy."""
        return self._potentialEnergy() * self._kineticEnergy()

    def isAtPosition(self, position: Position) -> bool:
        return self.position.x == position.x and \
            self.position.y == position.y and \
            self.position.z == position.z

    def isMoving(self) -> int:
        return bool(self.velocity.x or self.velocity.y or self.velocity.z)

    def _potentialEnergy(self) -> int:
        return abs(self.position.x) + abs(self.position.y) + abs(self.position.z)

    def _kineticEnergy(self) -> int:
        return abs(self.velocity.x) + abs(self.velocity.y) + abs(self.velocity.z)


class System:
    def __init__(self, requiredSteps: int) -> None:
        self.stars: List[Star] = []
        self.starsIntial: List[Star] = []
        self.requiredSteps = requiredSteps

    def __repr__(self) -> str:
        return '\n'.join(star.__repr__() for star in self.stars)

    def addStar(self, star: Star) -> None:
        self.stars.append(deepcopy(star))
        self.starsIntial.append(deepcopy(star))

    def reset(self) -> None:
        """Reset the whole system to its original states."""
        self.stars = deepcopy(self.starsIntial)

    def runSimulation(self) -> None:
        """Run the simulation with the specified number of steps."""
        for i in range(self.requiredSteps):
            self._updateSystemByOneStep()

    def getTotalEnergy(self) -> int:
        """Returns total energy of the system."""
        return sum(s.energy() for s in self.stars)

    def getSystemCycle(self) -> int:
        """
        Speed up the process by compute the cycle for each dimension, then
        return their least common multiple.
        """
        count = 0   # Steps count
        xCycle = yCycle = zCycle = 0    # Cycle on each dimension
        while not (xCycle and yCycle and zCycle):
            count += 1
            self._updateSystemByOneStep()

            if not xCycle and self._isSystemAtInitialStateOnDimension('x'):
                xCycle = count
            if not yCycle and self._isSystemAtInitialStateOnDimension('y'):
                yCycle = count
            if not zCycle and self._isSystemAtInitialStateOnDimension('z'):
                zCycle = count

        return lcm(xCycle, lcm(yCycle, zCycle))

    def _updateSystemByOneStep(self) -> None:
        # Clear gravitational values to recompute
        for star in self.stars:
            star.gravity = Gravity()

        # Compute and sum up g-force for every pair of stars
        for star1, star2 in combinations(self.stars, 2):
            star1.updateGForceForPair(star2)

        # Update velocity and position for each star
        for star in self.stars:
            star.updateVelocity()
            star.updatePosition()

    def _isSystemAtInitialStateOnDimension(self, dimension: str) -> bool:
        """
        Checks whether, on the specified dimension, the system has returned to
        its original state.
        """
        return all(
            star.position.__dict__[dimension] == starInit.position.__dict__[dimension]
            and star.velocity.__dict__[dimension] == starInit.velocity.__dict__[dimension]
            for star, starInit in zip(self.stars, self.starsIntial)
        )


class Solution:
    def __init__(self, inputFilePath: str, requiredSteps: int) -> None:
        self.system = System(requiredSteps)

        # Parse input file
        with open(inputFilePath, 'r') as fd:
            for line in fd:
                line = line.strip()
                if not line:
                    continue    # Ignore blank lines

                matchObj = INPUT_REGEXP.search(line)
                if matchObj is None:
                    raise Exception(f'Invalid input format ("{line}")')

                newStar = Star(
                    Position(*[int(val) for val in matchObj.group(1, 2, 3)]),
                    Velocity()
                )
                self.system.addStar(newStar)

    def solvePart1(self) -> int:
        self.system.runSimulation()
        return self.system.getTotalEnergy()

    def solvePart2(self) -> int:
        self.system.reset()
        return self.system.getSystemCycle()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Solution to day 12's problem")
    parser.add_argument('file', help='path to input file')
    parser.add_argument('steps', type=int, help='number of required steps')
    args = parser.parse_args()

    sol = Solution(args.file, args.steps)
    print(f'Part 1: {sol.solvePart1()}')
    print(f'Part 2: {sol.solvePart2()}')
