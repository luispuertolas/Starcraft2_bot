import sc2
from sc2.position import Point2
from sc2.unit import Unit
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import UnitTypeId
from sc2.constants import (SUPPLYDEPOT, BARRACKS, COMMANDCENTER, SCV, REFINERY,
                           STARPORT, FACTORY, ARMORY, ENGINEERINGBAY, MARINE,
                           HELLION, MEDIVAC, VIKINGFIGHTER)


class MyBot(sc2.BotAI):
    def __init__(self):
        self.worker_limit = 50
        self.building_spacing = 3  # Minimum spacing between buildings
        self.marine_limit = 50
        self.hellion_limit = 20
        self.transport_limit = 8
        self.viking_limit = 20

    async def on_step(self, iteration):
        await self.build_workers()
        await self.harvest_resources()
        await self.build_supply()
        await self.build_refinery()
        await self.build_barracks()
        await self.expand_base()
        await self.build_factory()
        await self.build_starport()
        await self.build_armories()
        await self.build_engineering_bays()        
        await self.build_marines()
        await self.build_hellions()
        await self.build_medivacs()
        await self.build_vikings()
        await self.defend_if_attacked()
        
    async def manage_workers(self):
        for worker in self.workers.idle:
            if self.start_location.distance_to(worker) > 10:
                closest_mineral_patch = self.state.mineral_field.closest_to(worker)
                self.do(worker.gather(closest_mineral_patch))
            
    async def harvest_resources(self):
        await self.distribute_workers()
        await self.manage_workers()

    async def defend_if_attacked(self):
        structures = self.units.structure
        if not structures:
            return
        enemy_units_nearby = self.known_enemy_units.closer_than(15, structures.random.position)
        idle_combat_units = self.units.filter(lambda unit: unit.can_attack_ground and unit.is_idle)
        if enemy_units_nearby.exists and idle_combat_units.exists:
            target = enemy_units_nearby.closest_to(structures.random.position)
            for unit in idle_combat_units:
                await self.do(unit.attack(target.position))

            
    def has_space_to_build(self, position, building_spacing):
        for structure in self.units.structure:
            if structure.position.distance_to(position) < building_spacing:
                return False
        return True

    async def build_workers(self):
        for cc in self.townhalls.ready.idle:
            if self.can_afford(SCV):
                await self.do(cc.train(SCV))

    async def build_supply(self):
        if self.supply_left < 5 and not self.already_pending(SUPPLYDEPOT):
            ccs = self.townhalls.ready
            if ccs.exists:
                if self.can_afford(SUPPLYDEPOT):
                    position = await self.find_placement(
                        SUPPLYDEPOT,
                        near=ccs.first.position,
                        placement_step=1,
                        max_distance=10,
                    )
                    if position and self.has_space_to_build(position, self.building_spacing):
                        await self.build(SUPPLYDEPOT, position)

    async def build_refinery(self):
        for cc in self.townhalls.ready:
            vgs = self.state.vespene_geyser.closer_than(20.0, cc)
            for vg in vgs:
                if not self.can_afford(REFINERY):
                    break
                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break
                if not self.units(REFINERY).closer_than(1.0, vg).exists:
                    await self.do(worker.build(REFINERY, vg))

    async def build_barracks(self):
        if (
            self.townhalls.ready.exists
            and self.units(BARRACKS).amount < 2
            and self.can_afford(BARRACKS)
            and not self.already_pending(BARRACKS)
        ):
            position = await self.find_placement(
                BARRACKS,
                near=self.townhalls.first.position,
                placement_step=1,
                max_distance=10,
            )
            if position and self.has_space_to_build(position, self.building_spacing):
                await self.build(BARRACKS, position)

    async def build_starport(self):
        if (
            self.units(BARRACKS).ready.exists
            and self.units(STARPORT).amount < 2
            and self.can_afford(STARPORT)
            and not self.already_pending(STARPORT)
        ):
            position = await self.find_placement(
                STARPORT,
                near=self.townhalls.first.position,
                placement_step=1,
                max_distance=10,
            )
            if position and self.has_space_to_build(position, self.building_spacing):
                await self.build(STARPORT, position)

    async def build_factory(self):
        if (
            self.units(BARRACKS).ready.exists
            and self.units(FACTORY).amount < 2
            and self.can_afford(FACTORY)
            and not self.already_pending(FACTORY)
        ):
            if len(self.townhalls) >= 2:
                position = await self.find_placement(FACTORY, near=self.townhalls[1].position, placement_step=1, max_distance=10,)
                if position and self.has_space_to_build(position, self.building_spacing):
                    await self.build(FACTORY, position)

    async def build_armories(self):
        if (
            self.units(FACTORY).ready.exists
            and self.units(ARMORY).amount < 3
            and self.can_afford(ARMORY)
            and not self.already_pending(ARMORY)
        ):
            position = await self.find_placement(
                ARMORY,
                near=self.townhalls[1].position,
                placement_step=1,
                max_distance=10,
            )
            if position and self.has_space_to_build(position, self.building_spacing):
                await self.build(ARMORY, position)

    async def build_engineering_bays(self):
        if (
            self.units(COMMANDCENTER).ready.exists
            and len(self.townhalls) >= 3
            and self.units(ENGINEERINGBAY).amount < 2
            and self.can_afford(ENGINEERINGBAY)
            and not self.already_pending(ENGINEERINGBAY)
        ):
            position = await self.find_placement(
                ENGINEERINGBAY,
                near=self.townhalls[2].position,
                placement_step=1,
                max_distance=10,
            )
            if position and self.has_space_to_build(position, self.building_spacing):
                await self.build(ENGINEERINGBAY, position)

    async def expand_base(self):
        if (
            len(self.townhalls) < 3
            and self.can_afford(UnitTypeId.COMMANDCENTER)
            and not self.already_pending(UnitTypeId.COMMANDCENTER)
        ):
            closest_expansion = await self.get_next_expansion
            if closest_expansion:
                worker = self.select_build_worker(self.townhalls.first)  # Use the first command center as a reference
                if worker and self.can_afford(UnitTypeId.COMMANDCENTER):
                    position = await self.find_placement(UnitTypeId.COMMANDCENTER, near=closest_expansion)
                    if position and self.has_space_to_build(position, self.building_spacing):
                        await self.build(UnitTypeId.COMMANDCENTER, position)

    async def build_marines(self):
        if (
            self.units(BARRACKS).ready.exists
            and self.units(MARINE).amount < self.marine_limit
        ):
            for barracks in self.units(BARRACKS).ready.idle:
                if self.can_afford(MARINE):
                    await self.do(barracks.train(MARINE))

    async def build_hellions(self):
        if (
            self.units(FACTORY).ready.exists
            and self.units(HELLION).amount < self.hellion_limit
        ):
            for factory in self.units(FACTORY).ready.idle:
                if self.can_afford(HELLION):
                    await self.do(factory.train(HELLION))

    async def build_medivacs(self):
        if (
            self.units(STARPORT).ready.exists
            and self.units(MEDIVAC).amount < self.transport_limit
        ):
            for starport in self.units(STARPORT).ready.idle:
                if self.can_afford(MEDIVAC):
                    await self.do(starport.train(MEDIVAC))

    async def build_vikings(self):
        if (
            self.units(STARPORT).ready.exists
            and self.units(VIKINGFIGHTER).amount < self.viking_limit
        ):
            for starport in self.units(STARPORT).ready.idle:
                if self.can_afford(VIKINGFIGHTER):
                    await self.do(starport.train(VIKINGFIGHTER))

    async def get_next_expansion(self):
        expansions = self.expansion_locations
        for location in expansions:
            if not self.units(COMMANDCENTER).closer_than(10, location).exists:
                return location
        return None


def main():
    run_game(maps.get("AbyssalReefLE"), [
        Bot(Race.Terran, MyBot()),
        Computer(Race.Protoss, Difficulty.Hard)
    ], realtime=False)


if __name__ == '__main__':
    main()
