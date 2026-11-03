import json, os, requests, argparse, datetime, math, io, operator, re
from io import BytesIO
import numpy as np
from typing import cast
import matplotlib.pyplot as plt
from matplotlib.projections.polar import PolarAxes
import pandas as pd

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

WIDTH, HEIGHT = A4

MARGIN = 5*mm

parser = argparse.ArgumentParser(description='Analyze your Minecraft World.')
parser.add_argument('world_name', type=str, help='World Name')
parser.add_argument('-f', '--file', type=str, default="./", help='Change the save location of the report file. Default: "./"')
parser.add_argument('-n', '--name', type=str, default="report", help='Name of the report file. Default: "report"')

class PDFReport:
    def __init__(self, output_path, output_name, player_name, world_name):
        self.output_path = output_path
        self.output_name = output_name
        self.player_name = player_name
        self.world_name = world_name
        try:
            self.canvas = canvas.Canvas(f'{output_path}{output_name}.pdf', pagesize=A4)
        except:
            raise ValueError("Can't create a file at that location.")

    def add_header(self, page):
        self.canvas.setFont("Arial", 22)
        self.canvas.drawString(MARGIN, HEIGHT-2*MARGIN, "Minestats")
        self.canvas.setFont("Arial", 12)
        self.canvas.drawString(MARGIN, HEIGHT-3*MARGIN, page)

    def add_stat_info(self, name, world_name, player_head, date):
        self.canvas.setFont("Arial", 26)
        self.canvas.drawString(2*MARGIN+135, A4[1]*0.75+125, name)
        self.canvas.setFont("Arial", 18)
        self.canvas.drawString(2*MARGIN+135, A4[1]*0.75+100, f'World: {world_name}')
        self.canvas.setFont("Arial", 12)
        self.canvas.drawString(2*MARGIN+135, A4[1]*0.75+MARGIN, f'Analysis Date: {date.strftime("%d.%m.%y")}')
        player_head = ImageReader(BytesIO(player_head))
        self.canvas.drawImage(
            player_head,
            x=MARGIN,
            y=A4[1]*0.75+MARGIN,
            width=135,
            height=135,
            preserveAspectRatio=True
        )

    def add_kpi_overview(self, stats):
        sec = stats.get('minecraft:custom', {}).get('minecraft:play_time', 0)//20
        self.add_kpi_stat(1/6, 5/16, "Time Played", str(datetime.timedelta(seconds=sec)))
        blocks_mined = sum(stats.get('minecraft:mined', {"": 0}).values())
        self.add_kpi_stat(1/2, 5/16, "Blocks Mined", f'{blocks_mined:,}')
        mobs_killed = stats.get("minecraft:custom", {}).get("minecraft:mob_kills", 0)
        self.add_kpi_stat(5/6, 5/16, "Mobs killed", f'{mobs_killed:,}')
        excluded = {
            "minecraft:fall_one_cm",
            "minecraft:climb_one_cm",
        }
        distance = sum(value for stat, value in stats.get("minecraft:custom", {}).items() if stat.endswith("_one_cm") and stat not in excluded)
        self.add_kpi_stat(1/6, 7/16, "Distance", f'{distance/100_000:,.2f} km')
        deaths = stats.get("minecraft:custom", {}).get("minecraft:deaths", 0)
        self.add_kpi_stat(1/2, 7/16, "Deaths", f'{deaths:,}')
        items_crafted = sum(stats.get('minecraft:crafted', {"": 0}).values())
        self.add_kpi_stat(5/6, 7/16, "Items Crafted", f'{items_crafted:,}')

    def add_kpi_stat(self, x, y, stat_name, value):
        self.canvas.setFont("Arial", 26)
        self.canvas.drawCentredString(A4[0]*x, (1-y)*A4[1]+10, stat_name+":")
        self.canvas.setFont("Arial", 20)
        self.canvas.drawCentredString(A4[0]*x, (1-y)*A4[1]-20, value)

    def add_radar_chart(self, data):
        values, labels  = data

        labels = np.asarray(labels)
        values = np.asarray(values, dtype=float)

        if labels.ndim != 1 or values.ndim != 1:
            raise ValueError("labels and values must both be 1D arrays")

        if len(labels) != len(values):
            raise ValueError("labels and values must have the same length")

        n = len(labels)

        theta = np.linspace(0, 2 * np.pi, n, endpoint=False)

        theta_closed = np.concatenate([theta, [theta[0]]])
        values_closed = np.concatenate([values, [values[0]]])

        fig, ax = plt.subplots(
            figsize=(7, 7),
            subplot_kw={"projection": "polar"}
        )

        ax = cast(PolarAxes, ax)

        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)

        ax.set_xticks(theta)
        ax.set_xticklabels(labels)

        ax.plot(theta_closed, values_closed, linewidth=2)
        ax.fill(theta_closed, values_closed, alpha=0.25)

        ax.set_title("Playstyle", pad=20)

        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300)
        img_buffer.seek(0)
        plt.close(fig)

        chart_img = ImageReader(img_buffer)
        size = A4[0]/2 - 2*MARGIN
        self.canvas.drawImage(chart_img, MARGIN, 1/6*A4[1]+MARGIN/2, width=size, height=size)

    def add_highlight_stats(self, stats, USED_ITEMS):
        USED_ITEMS = [
            # Tools
            "minecraft:wooden_shovel",
            "minecraft:wooden_pickaxe",
            "minecraft:wooden_axe",
            "minecraft:wooden_hoe",
            "minecraft:copper_shovel",
            "minecraft:copper_pickaxe",
            "minecraft:copper_axe",
            "minecraft:copper_hoe",
            "minecraft:stone_shovel",
            "minecraft:stone_pickaxe",
            "minecraft:stone_axe",
            "minecraft:stone_hoe",
            "minecraft:golden_shovel",
            "minecraft:golden_pickaxe",
            "minecraft:golden_axe",
            "minecraft:golden_hoe",
            "minecraft:iron_shovel",
            "minecraft:iron_pickaxe",
            "minecraft:iron_axe",
            "minecraft:iron_hoe",
            "minecraft:diamond_shovel",
            "minecraft:diamond_pickaxe",
            "minecraft:diamond_axe",
            "minecraft:diamond_hoe",
            "minecraft:netherite_shovel",
            "minecraft:netherite_pickaxe",
            "minecraft:netherite_axe",
            "minecraft:netherite_hoe",

            "minecraft:shears",
            "minecraft:flint_and_steel",
            "minecraft:fishing_rod",
            "minecraft:brush",

            # Weapons
            "minecraft:wooden_sword",
            "minecraft:copper_sword",
            "minecraft:stone_sword",
            "minecraft:golden_sword",
            "minecraft:iron_sword",
            "minecraft:diamond_sword",
            "minecraft:netherite_sword",

            "minecraft:wooden_spear",
            "minecraft:copper_spear",
            "minecraft:stone_spear",
            "minecraft:golden_spear",
            "minecraft:iron_spear",
            "minecraft:diamond_spear",
            "minecraft:netherite_spear",

            "minecraft:bow",
            "minecraft:crossbow",
            "minecraft:trident",
            "minecraft:mace",

            # Buckets
            "minecraft:bucket",
            "minecraft:water_bucket",
            "minecraft:lava_bucket",
            "minecraft:powder_snow_bucket",
            "minecraft:milk_bucket",
            "minecraft:cod_bucket",
            "minecraft:salmon_bucket",
            "minecraft:pufferfish_bucket",
            "minecraft:tropical_fish_bucket",
            "minecraft:axolotl_bucket",
            "minecraft:tadpole_bucket",
            "minecraft:sulfur_cube_bucket",

            # Utility
            "minecraft:carrot_on_a_stick",
            "minecraft:warped_fungus_on_a_stick",
            "minecraft:spyglass",
            "minecraft:goat_horn",
            "minecraft:ender_pearl",
            "minecraft:ender_eye",
            "minecraft:firework_rocket",
            "minecraft:fire_charge",
            "minecraft:wind_charge",
            "minecraft:experience_bottle",
            "minecraft:glass_bottle",
            "minecraft:lead",
            "minecraft:name_tag",

            # Throwable / ranged consumables
            "minecraft:snowball",
            "minecraft:egg",
            "minecraft:blue_egg",
            "minecraft:brown_egg",
            "minecraft:splash_potion",
            "minecraft:lingering_potion",

            # Storage / interactive items
            "minecraft:bundle",
            "minecraft:white_bundle",
            "minecraft:orange_bundle",
            "minecraft:magenta_bundle",
            "minecraft:light_blue_bundle",
            "minecraft:yellow_bundle",
            "minecraft:lime_bundle",
            "minecraft:pink_bundle",
            "minecraft:gray_bundle",
            "minecraft:light_gray_bundle",
            "minecraft:cyan_bundle",
            "minecraft:purple_bundle",
            "minecraft:blue_bundle",
            "minecraft:brown_bundle",
            "minecraft:green_bundle",
            "minecraft:red_bundle",
            "minecraft:black_bundle",

            # Farming / item actions
            "minecraft:bone_meal",
            "minecraft:white_dye",
            "minecraft:orange_dye",
            "minecraft:magenta_dye",
            "minecraft:light_blue_dye",
            "minecraft:yellow_dye",
            "minecraft:lime_dye",
            "minecraft:pink_dye",
            "minecraft:gray_dye",
            "minecraft:light_gray_dye",
            "minecraft:cyan_dye",
            "minecraft:purple_dye",
            "minecraft:blue_dye",
            "minecraft:brown_dye",
            "minecraft:green_dye",
            "minecraft:red_dye",
            "minecraft:black_dye",
        ]

        most_mined = max(stats.get("minecraft:mined", {"None": 0}).items(), key=operator.itemgetter(1))[0].removeprefix("minecraft:").replace("_", " ").title()
        placed = {stat: value for stat, value in stats.get("minecraft:used", {}).items() if stat not in USED_ITEMS}
        most_placed = max(placed.items(), key=operator.itemgetter(1))[0].removeprefix("minecraft:").replace("_", " ").title()
        used = {stat: value for stat, value in stats.get("minecraft:used", {}).items() if stat in USED_ITEMS}
        most_used = max(used.items(), key=operator.itemgetter(1))[0].removeprefix("minecraft:").replace("_", " ").title()
        most_killed = max(stats.get("minecraft:killed", {"None": 0}).items(), key=operator.itemgetter(1))[0].removeprefix("minecraft:").replace("_", " ").title()
        main_travel = get_main_travel(stats)

        texts = [
            "Most Mined: "+most_mined,
            "Most Placed: "+most_placed,
            "Most Used: "+most_used,
            "Most Killed: "+most_killed,
            "Main Travel: "+main_travel,
        ]

        left = A4[0] / 2
        right = A4[0]
        bottom = A4[1] / 6
        top = A4[1] / 2

        x = left + MARGIN

        spacing = (top - bottom) / len(texts)

        self.canvas.setFont("Arial", 16)

        for i, text in enumerate(texts):
            y = top - (i + 0.5) * spacing
            if len(text) <= 30:
                self.canvas.drawString(x, y, str(text))
            else:
                self.canvas.drawString(x, y, str(text[:30]))
                self.canvas.drawString(x, y-15, str(text[30:]))

    def add_fun_fact(self, stats):
        self.canvas.setFont("Arial", 24)
        self.canvas.drawCentredString(A4[0]/2, A4[1]/6-30, "Fun Fact")
        excluded = {
            "minecraft:fall_one_cm",
            "minecraft:climb_one_cm",
        }
        km = sum(value for stat, value in stats.get("minecraft:custom", {}).items() if stat.endswith("_one_cm") and stat not in excluded)/100000
        h = stats.get('minecraft:custom', {}).get('minecraft:play_time', 1)/(20*60*60)
        kmh = km//h
        world_circumnavigates = km/40075
        jumps = stats.get('minecraft:custom', {}).get('minecraft:jump', 0)
        mount_everests = jumps / 8848.86
        mob_kills = stats.get("minecraft:custom", {}).get("minecraft:mob_kills", 0)
        if kmh > 10:
            fact = f"You've travelled {km/100_000:,.2f} km!"
            subtext = f"That's almost {kmh} km/h ({0.621371*kmh} mph) on average."
        elif world_circumnavigates > 1:
            fact = f"You've travelled {km/100_000:,.2f} km!"
            subtext = f"That's like you've circumnavigated the world {world_circumnavigates} times"
        elif mount_everests > 1:
            fact = f"You've jumped {jumps} times!"
            subtext = f"By that time you could've climbed Mount Everest {mount_everests:,.2f} times!"
        else:
            fact = "Mob Hunter"
            subtext = f"You've killed {mob_kills} mobs!"
        self.canvas.setFont("Arial", 20)
        self.canvas.drawCentredString(A4[0]/2, A4[1]/6-70, fact)
        self.canvas.setFont("Arial", 16)
        self.canvas.drawCentredString(A4[0]/2, A4[1]/6-100, subtext)

    def add_mined_chart(self, stats):
        fig, ax = plt.subplots()

        mined_stats = dict(sorted(stats.get("minecraft:mined", {}).items(), key=lambda item: item[1], reverse=True)[:10])

        blocks = list(map(lambda x: x.removeprefix("minecraft:").replace("_", " ").title(),mined_stats.keys()))
        mined = list(mined_stats.values())

        ax.barh(blocks, mined, align='center')
        ax.yaxis.set_inverted(True)
        ax.set_label('Blocks Mined')
        ax.set_title('Most Mined Blocks')

        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300)
        img_buffer.seek(0)
        plt.close(fig)
        chart_img = ImageReader(img_buffer)
        size = A4[0]/2 - 2*MARGIN
        self.canvas.drawImage(chart_img, MARGIN/2, A4[1]-A4[0]/2+MARGIN, width=size, height=size, preserveAspectRatio=True)

    def add_placed_chart(self, stats, USED_ITEMS):
        fig, ax = plt.subplots()

        placed = {stat: value for stat, value in stats.get("minecraft:used", {}).items() if stat not in USED_ITEMS}
    
        placed_stats = dict(sorted(placed.items(), key=lambda item: item[1], reverse=True)[:10])
    
        blocks = list(map(lambda x: x.removeprefix("minecraft:").replace("_", " ").title(),placed_stats.keys()))
        placed = list(placed_stats.values())
    
        ax.barh(blocks, placed, align='center')
        ax.yaxis.set_inverted(True)
        ax.set_label('Blocks Placed')
        ax.set_title('Most Placed Blocks')
    
        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300)
        img_buffer.seek(0)
        plt.close(fig)
        chart_img = ImageReader(img_buffer)
        size = A4[0]/2 - 2*MARGIN
        self.canvas.drawImage(chart_img, A4[0]/2+MARGIN/2, A4[1]-A4[0]/2+MARGIN, width=size, height=size, preserveAspectRatio=True)

    def add_ore_chart(self, stats):
        ORES = [
            "minecraft:coal_ore",
            "minecraft:deepslate_coal_ore",
            "minecraft:iron_ore",
            "minecraft:deepslate_iron_ore",
            "minecraft:copper_ore",
            "minecraft:deepslate_copper_ore",
            "minecraft:gold_ore",
            "minecraft:deepslate_gold_ore",
            "minecraft:redstone_ore",
            "minecraft:deepslate_redstone_ore",
            "minecraft:lapis_ore",
            "minecraft:deepslate_lapis_ore",
            "minecraft:diamond_ore",
            "minecraft:deepslate_diamond_ore",
            "minecraft:emerald_ore",
            "minecraft:deepslate_emerald_ore",
            "minecraft:nether_gold_ore",
            "minecraft:nether_quartz_ore",
            "minecraft:ancient_debris"
        ]

        ORE_COLORS = {
            "Quartz": "#f0efe8",
            "Diamond": "#62ede4",
            "Iron": "#dcdcdc",
            "Lapis": "#1500ff",
            "Redstone": "#b80909",
            "Copper": "#c06c50",
            "Gold": "#f6d03e",
            "Coal": "#0f0f0f",
            "Ancient Debris": "#604038",
            "Other": "#9c9c9c"
        }

        ore_mined = {stat: value for stat, value in stats.get("minecraft:mined", {}).items() if stat  in ORES}
        ore_placed = {stat: value for stat, value in stats.get("minecraft:used", {}).items() if stat  in ORES}

        ore_stats = {key: ore_mined[key] - ore_placed.get(key, 0) for key in ore_mined.keys()}

        ore_stats = {stat.removeprefix("minecraft:").removeprefix("nether_").removesuffix("_ore").replace("_", " ").title(): value for stat, value in ore_stats.items()}

        material_ore_stats = {}
        for ore, value in ore_stats.items():
            material = ore.removeprefix("Deepslate ")
            material_ore_stats[material] = material_ore_stats.get(material, 0) + value

        material_ore_stats = dict(sorted(material_ore_stats.items(), key=lambda item: item[1], reverse=True))

        labels = list(material_ore_stats.keys())
        mined = list(material_ore_stats.values())

        df = pd.DataFrame({"Labels": labels, "Mined": mined})

        threshold = 0.02*df["Mined"].sum()

        mask = df["Mined"] < threshold

        df_grouped = df.copy()
        df_grouped.loc[mask, "Labels"] = "Other"
        df_grouped = df_grouped.groupby('Labels', as_index=False).sum()

        colors = [ORE_COLORS[material] for material in df_grouped["Labels"]]

        fig, ax = plt.subplots()

        ax.pie(df_grouped["Mined"], labels=list(df_grouped["Labels"]), colors=colors)

        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300)
        img_buffer.seek(0)
        plt.close(fig)
        chart_img = ImageReader(img_buffer)
        size = A4[0]/2 - 2*MARGIN
        self.canvas.drawImage(chart_img, MARGIN/2, A4[1]-A4[0]+MARGIN, width=size, height=size, preserveAspectRatio=True)

    def add_killed_chart(self, stats):
        fig, ax = plt.subplots()
    
        mined_stats = dict(sorted(stats.get("minecraft:killed", {}).items(), key=lambda item: item[1], reverse=True)[:5])
    
        blocks = list(map(lambda x: x.removeprefix("minecraft:").replace("_", " ").title(),mined_stats.keys()))
        mined = list(mined_stats.values())
    
        bars = ax.bar(blocks, mined, align='center')
        ax.set_label('Mobs Killed')
        ax.set_title('Most Mobs Killed')
        ax.bar_label(bars, fontsize=14)
    
        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300)
        img_buffer.seek(0)
        plt.close(fig)
        chart_img = ImageReader(img_buffer)
        size = A4[0]/2 - 2*MARGIN
        self.canvas.drawImage(chart_img, A4[0]/2+MARGIN/2, A4[1]-A4[0]+MARGIN, width=size, height=size, preserveAspectRatio=True)

    def add_advancement_chart(self, stats):
        fig, ax = plt.subplots(figsize=(17, 6.5))

        biomes = stats["minecraft:adventure/adventuring_time"]["criteria"]

        discoveries = []

        for biome, timestamp in biomes.items():
            date = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %z")

            biome = biome.removeprefix("minecraft:").replace("_", " ").title()

            discoveries.append((date, biome))

        discoveries.sort(key=lambda x: x[0])

        dates = [date for date, biome in discoveries]
        discovered_count = range(1, len(discoveries) + 1)

        plt.step(
            dates,
            discovered_count,
            where="post"
        )

        ax.tick_params(axis="both", labelsize=16)

        ax.set_xlabel("Date", fontsize=18)
        ax.set_ylabel("Biomes Discovered", fontsize=18)
        ax.set_title("Adventuring Time Progress", fontsize=22, pad=15)

        fig.autofmt_xdate(rotation=30)

        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300)
        img_buffer.seek(0)
        plt.close(fig)
        chart_img = ImageReader(img_buffer)
        self.canvas.drawImage(chart_img, MARGIN, MARGIN, width=A4[0]-MARGIN*2, height=A4[1]-A4[0]-MARGIN*2, preserveAspectRatio=True, anchor='c')

    def add_border(self, y):
        self.canvas.setLineWidth(2.5)
        self.canvas.line(0, (1-y)*A4[1], A4[0], (1-y)*A4[1])

    def add_divider(self, y1, y2):
        self.canvas.setLineWidth(2.5)
        self.canvas.line(A4[0]/2, y1*A4[1], A4[0]/2, y2*A4[1])


    def get_radar_chart_data(self, stats):
        REDSTONE_COMPONENTS = [
            "minecraft:redstone",
            "minecraft:redstone_torch",
            "minecraft:repeater",
            "minecraft:comparator",
            "minecraft:redstone_block",
            "minecraft:lever",
            "minecraft:stone_button",
            "minecraft:polished_blackstone_button",
            "minecraft:oak_button",
            "minecraft:spruce_button",
            "minecraft:birch_button",
            "minecraft:jungle_button",
            "minecraft:acacia_button",
            "minecraft:dark_oak_button",
            "minecraft:mangrove_button",
            "minecraft:cherry_button",
            "minecraft:bamboo_button",
            "minecraft:pale_oak_button",
            "minecraft:poplar_button",
            "minecraft:crimson_button",
            "minecraft:warped_button",
            "minecraft:stone_pressure_plate",
            "minecraft:polished_blackstone_pressure_plate",
            "minecraft:light_weighted_pressure_plate",
            "minecraft:heavy_weighted_pressure_plate",
            "minecraft:oak_pressure_plate",
            "minecraft:spruce_pressure_plate",
            "minecraft:birch_pressure_plate",
            "minecraft:jungle_pressure_plate",
            "minecraft:acacia_pressure_plate",
            "minecraft:dark_oak_pressure_plate",
            "minecraft:mangrove_pressure_plate",
            "minecraft:cherry_pressure_plate",
            "minecraft:bamboo_pressure_plate",
            "minecraft:pale_oak_pressure_plate",
            "minecraft:poplar_pressure_plate",
            "minecraft:crimson_pressure_plate",
            "minecraft:warped_pressure_plate",
            "minecraft:target",
            "minecraft:tripwire_hook",
            "minecraft:daylight_detector",
            "minecraft:lightning_rod",
            "minecraft:sculk_sensor",
            "minecraft:calibrated_sculk_sensor",
            "minecraft:observer",
            "minecraft:piston",
            "minecraft:sticky_piston",
            "minecraft:slime_block",
            "minecraft:honey_block",
            "minecraft:hopper",
            "minecraft:dropper",
            "minecraft:dispenser",
            "minecraft:crafter",
            "minecraft:redstone_lamp",
            "minecraft:note_block",
            "minecraft:powered_rail",
            "minecraft:detector_rail",
            "minecraft:activator_rail",
            "minecraft:trapped_chest",
            "minecraft:tnt",
            "minecraft:copper_bulb",
            "minecraft:exposed_copper_bulb",
            "minecraft:weathered_copper_bulb",
            "minecraft:oxidized_copper_bulb",
            "minecraft:waxed_copper_bulb",
            "minecraft:waxed_exposed_copper_bulb",
            "minecraft:waxed_weathered_copper_bulb",
            "minecraft:waxed_oxidized_copper_bulb",
        ]
        BUILDING_BLOCKS = [
            "minecraft:stone",
            "minecraft:smooth_stone",
            "minecraft:stone_slab",
            "minecraft:stone_stairs",
            "minecraft:cobblestone",
            "minecraft:cobblestone_slab",
            "minecraft:cobblestone_stairs",
            "minecraft:cobblestone_wall",
            "minecraft:mossy_cobblestone",
            "minecraft:mossy_cobblestone_slab",
            "minecraft:mossy_cobblestone_stairs",
            "minecraft:mossy_cobblestone_wall",
            "minecraft:stone_bricks",
            "minecraft:stone_brick_slab",
            "minecraft:stone_brick_stairs",
            "minecraft:stone_brick_wall",
            "minecraft:mossy_stone_bricks",
            "minecraft:mossy_stone_brick_slab",
            "minecraft:mossy_stone_brick_stairs",
            "minecraft:mossy_stone_brick_wall",
            "minecraft:cracked_stone_bricks",
            "minecraft:chiseled_stone_bricks",
            "minecraft:granite",
            "minecraft:granite_slab",
            "minecraft:granite_stairs",
            "minecraft:granite_wall",
            "minecraft:polished_granite",
            "minecraft:polished_granite_slab",
            "minecraft:polished_granite_stairs",
            "minecraft:diorite",
            "minecraft:diorite_slab",
            "minecraft:diorite_stairs",
            "minecraft:diorite_wall",
            "minecraft:polished_diorite",
            "minecraft:polished_diorite_slab",
            "minecraft:polished_diorite_stairs",
            "minecraft:andesite",
            "minecraft:andesite_slab",
            "minecraft:andesite_stairs",
            "minecraft:andesite_wall",
            "minecraft:polished_andesite",
            "minecraft:polished_andesite_slab",
            "minecraft:polished_andesite_stairs",
            "minecraft:cobbled_deepslate",
            "minecraft:cobbled_deepslate_slab",
            "minecraft:cobbled_deepslate_stairs",
            "minecraft:cobbled_deepslate_wall",
            "minecraft:polished_deepslate",
            "minecraft:polished_deepslate_slab",
            "minecraft:polished_deepslate_stairs",
            "minecraft:polished_deepslate_wall",
            "minecraft:deepslate_bricks",
            "minecraft:deepslate_brick_slab",
            "minecraft:deepslate_brick_stairs",
            "minecraft:deepslate_brick_wall",
            "minecraft:cracked_deepslate_bricks",
            "minecraft:deepslate_tiles",
            "minecraft:deepslate_tile_slab",
            "minecraft:deepslate_tile_stairs",
            "minecraft:deepslate_tile_wall",
            "minecraft:cracked_deepslate_tiles",
            "minecraft:chiseled_deepslate",
            "minecraft:tuff",
            "minecraft:tuff_slab",
            "minecraft:tuff_stairs",
            "minecraft:tuff_wall",
            "minecraft:polished_tuff",
            "minecraft:polished_tuff_slab",
            "minecraft:polished_tuff_stairs",
            "minecraft:polished_tuff_wall",
            "minecraft:tuff_bricks",
            "minecraft:tuff_brick_slab",
            "minecraft:tuff_brick_stairs",
            "minecraft:tuff_brick_wall",
            "minecraft:chiseled_tuff",
            "minecraft:chiseled_tuff_bricks",
            "minecraft:bricks",
            "minecraft:brick_slab",
            "minecraft:brick_stairs",
            "minecraft:brick_wall",
            "minecraft:packed_mud",
            "minecraft:mud_bricks",
            "minecraft:mud_brick_slab",
            "minecraft:mud_brick_stairs",
            "minecraft:mud_brick_wall",
            "minecraft:sandstone",
            "minecraft:sandstone_slab",
            "minecraft:sandstone_stairs",
            "minecraft:sandstone_wall",
            "minecraft:cut_sandstone",
            "minecraft:cut_sandstone_slab",
            "minecraft:smooth_sandstone",
            "minecraft:smooth_sandstone_slab",
            "minecraft:smooth_sandstone_stairs",
            "minecraft:chiseled_sandstone",
            "minecraft:red_sandstone",
            "minecraft:red_sandstone_slab",
            "minecraft:red_sandstone_stairs",
            "minecraft:red_sandstone_wall",
            "minecraft:cut_red_sandstone",
            "minecraft:cut_red_sandstone_slab",
            "minecraft:smooth_red_sandstone",
            "minecraft:smooth_red_sandstone_slab",
            "minecraft:smooth_red_sandstone_stairs",
            "minecraft:chiseled_red_sandstone",
            "minecraft:nether_bricks",
            "minecraft:nether_brick_slab",
            "minecraft:nether_brick_stairs",
            "minecraft:nether_brick_wall",
            "minecraft:nether_brick_fence",
            "minecraft:red_nether_bricks",
            "minecraft:red_nether_brick_slab",
            "minecraft:red_nether_brick_stairs",
            "minecraft:red_nether_brick_wall",
            "minecraft:cracked_nether_bricks",
            "minecraft:chiseled_nether_bricks",
            "minecraft:blackstone",
            "minecraft:blackstone_slab",
            "minecraft:blackstone_stairs",
            "minecraft:blackstone_wall",
            "minecraft:polished_blackstone",
            "minecraft:polished_blackstone_slab",
            "minecraft:polished_blackstone_stairs",
            "minecraft:polished_blackstone_wall",
            "minecraft:polished_blackstone_bricks",
            "minecraft:polished_blackstone_brick_slab",
            "minecraft:polished_blackstone_brick_stairs",
            "minecraft:polished_blackstone_brick_wall",
            "minecraft:cracked_polished_blackstone_bricks",
            "minecraft:chiseled_polished_blackstone",
            "minecraft:basalt",
            "minecraft:polished_basalt",
            "minecraft:smooth_basalt",
            "minecraft:quartz_block",
            "minecraft:quartz_slab",
            "minecraft:quartz_stairs",
            "minecraft:smooth_quartz",
            "minecraft:smooth_quartz_slab",
            "minecraft:smooth_quartz_stairs",
            "minecraft:quartz_bricks",
            "minecraft:quartz_pillar",
            "minecraft:chiseled_quartz_block",
            "minecraft:end_stone_bricks",
            "minecraft:end_stone_brick_slab",
            "minecraft:end_stone_brick_stairs",
            "minecraft:end_stone_brick_wall",
            "minecraft:purpur_block",
            "minecraft:purpur_pillar",
            "minecraft:purpur_slab",
            "minecraft:purpur_stairs",
            "minecraft:prismarine",
            "minecraft:prismarine_slab",
            "minecraft:prismarine_stairs",
            "minecraft:prismarine_wall",
            "minecraft:prismarine_bricks",
            "minecraft:prismarine_brick_slab",
            "minecraft:prismarine_brick_stairs",
            "minecraft:dark_prismarine",
            "minecraft:dark_prismarine_slab",
            "minecraft:dark_prismarine_stairs",
            "minecraft:resin_bricks",
            "minecraft:resin_brick_slab",
            "minecraft:resin_brick_stairs",
            "minecraft:resin_brick_wall",
            "minecraft:chiseled_resin_bricks",
            "minecraft:oak_log",
            "minecraft:stripped_oak_log",
            "minecraft:oak_wood",
            "minecraft:stripped_oak_wood",
            "minecraft:oak_planks",
            "minecraft:oak_slab",
            "minecraft:oak_stairs",
            "minecraft:oak_fence",
            "minecraft:oak_fence_gate",
            "minecraft:oak_door",
            "minecraft:oak_trapdoor",
            "minecraft:spruce_log",
            "minecraft:stripped_spruce_log",
            "minecraft:spruce_wood",
            "minecraft:stripped_spruce_wood",
            "minecraft:spruce_planks",
            "minecraft:spruce_slab",
            "minecraft:spruce_stairs",
            "minecraft:spruce_fence",
            "minecraft:spruce_fence_gate",
            "minecraft:spruce_door",
            "minecraft:spruce_trapdoor",
            "minecraft:birch_log",
            "minecraft:stripped_birch_log",
            "minecraft:birch_wood",
            "minecraft:stripped_birch_wood",
            "minecraft:birch_planks",
            "minecraft:birch_slab",
            "minecraft:birch_stairs",
            "minecraft:birch_fence",
            "minecraft:birch_fence_gate",
            "minecraft:birch_door",
            "minecraft:birch_trapdoor",
            "minecraft:jungle_log",
            "minecraft:stripped_jungle_log",
            "minecraft:jungle_wood",
            "minecraft:stripped_jungle_wood",
            "minecraft:jungle_planks",
            "minecraft:jungle_slab",
            "minecraft:jungle_stairs",
            "minecraft:jungle_fence",
            "minecraft:jungle_fence_gate",
            "minecraft:jungle_door",
            "minecraft:jungle_trapdoor",
            "minecraft:acacia_log",
            "minecraft:stripped_acacia_log",
            "minecraft:acacia_wood",
            "minecraft:stripped_acacia_wood",
            "minecraft:acacia_planks",
            "minecraft:acacia_slab",
            "minecraft:acacia_stairs",
            "minecraft:acacia_fence",
            "minecraft:acacia_fence_gate",
            "minecraft:acacia_door",
            "minecraft:acacia_trapdoor",
            "minecraft:dark_oak_log",
            "minecraft:stripped_dark_oak_log",
            "minecraft:dark_oak_wood",
            "minecraft:stripped_dark_oak_wood",
            "minecraft:dark_oak_planks",
            "minecraft:dark_oak_slab",
            "minecraft:dark_oak_stairs",
            "minecraft:dark_oak_fence",
            "minecraft:dark_oak_fence_gate",
            "minecraft:dark_oak_door",
            "minecraft:dark_oak_trapdoor",
            "minecraft:mangrove_log",
            "minecraft:stripped_mangrove_log",
            "minecraft:mangrove_wood",
            "minecraft:stripped_mangrove_wood",
            "minecraft:mangrove_planks",
            "minecraft:mangrove_slab",
            "minecraft:mangrove_stairs",
            "minecraft:mangrove_fence",
            "minecraft:mangrove_fence_gate",
            "minecraft:mangrove_door",
            "minecraft:mangrove_trapdoor",
            "minecraft:cherry_log",
            "minecraft:stripped_cherry_log",
            "minecraft:cherry_wood",
            "minecraft:stripped_cherry_wood",
            "minecraft:cherry_planks",
            "minecraft:cherry_slab",
            "minecraft:cherry_stairs",
            "minecraft:cherry_fence",
            "minecraft:cherry_fence_gate",
            "minecraft:cherry_door",
            "minecraft:cherry_trapdoor",
            "minecraft:pale_oak_log",
            "minecraft:stripped_pale_oak_log",
            "minecraft:pale_oak_wood",
            "minecraft:stripped_pale_oak_wood",
            "minecraft:pale_oak_planks",
            "minecraft:pale_oak_slab",
            "minecraft:pale_oak_stairs",
            "minecraft:pale_oak_fence",
            "minecraft:pale_oak_fence_gate",
            "minecraft:pale_oak_door",
            "minecraft:pale_oak_trapdoor",
            "minecraft:bamboo_block",
            "minecraft:stripped_bamboo_block",
            "minecraft:bamboo_planks",
            "minecraft:bamboo_slab",
            "minecraft:bamboo_stairs",
            "minecraft:bamboo_fence",
            "minecraft:bamboo_fence_gate",
            "minecraft:bamboo_door",
            "minecraft:bamboo_trapdoor",
            "minecraft:bamboo_mosaic",
            "minecraft:bamboo_mosaic_slab",
            "minecraft:bamboo_mosaic_stairs",
            "minecraft:poplar_log",
            "minecraft:stripped_poplar_log",
            "minecraft:poplar_wood",
            "minecraft:stripped_poplar_wood",
            "minecraft:poplar_planks",
            "minecraft:poplar_slab",
            "minecraft:poplar_stairs",
            "minecraft:poplar_fence",
            "minecraft:poplar_fence_gate",
            "minecraft:poplar_door",
            "minecraft:poplar_trapdoor",
            "minecraft:crimson_stem",
            "minecraft:stripped_crimson_stem",
            "minecraft:crimson_hyphae",
            "minecraft:stripped_crimson_hyphae",
            "minecraft:crimson_planks",
            "minecraft:crimson_slab",
            "minecraft:crimson_stairs",
            "minecraft:crimson_fence",
            "minecraft:crimson_fence_gate",
            "minecraft:crimson_door",
            "minecraft:crimson_trapdoor",
            "minecraft:warped_stem",
            "minecraft:stripped_warped_stem",
            "minecraft:warped_hyphae",
            "minecraft:stripped_warped_hyphae",
            "minecraft:warped_planks",
            "minecraft:warped_slab",
            "minecraft:warped_stairs",
            "minecraft:warped_fence",
            "minecraft:warped_fence_gate",
            "minecraft:warped_door",
            "minecraft:warped_trapdoor",
            "minecraft:white_wool",
            "minecraft:orange_wool",
            "minecraft:magenta_wool",
            "minecraft:light_blue_wool",
            "minecraft:yellow_wool",
            "minecraft:lime_wool",
            "minecraft:pink_wool",
            "minecraft:gray_wool",
            "minecraft:light_gray_wool",
            "minecraft:cyan_wool",
            "minecraft:purple_wool",
            "minecraft:blue_wool",
            "minecraft:brown_wool",
            "minecraft:green_wool",
            "minecraft:red_wool",
            "minecraft:black_wool",
            "minecraft:white_concrete",
            "minecraft:orange_concrete",
            "minecraft:magenta_concrete",
            "minecraft:light_blue_concrete",
            "minecraft:yellow_concrete",
            "minecraft:lime_concrete",
            "minecraft:pink_concrete",
            "minecraft:gray_concrete",
            "minecraft:light_gray_concrete",
            "minecraft:cyan_concrete",
            "minecraft:purple_concrete",
            "minecraft:blue_concrete",
            "minecraft:brown_concrete",
            "minecraft:green_concrete",
            "minecraft:red_concrete",
            "minecraft:black_concrete",
            "minecraft:terracotta",
            "minecraft:white_terracotta",
            "minecraft:orange_terracotta",
            "minecraft:magenta_terracotta",
            "minecraft:light_blue_terracotta",
            "minecraft:yellow_terracotta",
            "minecraft:lime_terracotta",
            "minecraft:pink_terracotta",
            "minecraft:gray_terracotta",
            "minecraft:light_gray_terracotta",
            "minecraft:cyan_terracotta",
            "minecraft:purple_terracotta",
            "minecraft:blue_terracotta",
            "minecraft:brown_terracotta",
            "minecraft:green_terracotta",
            "minecraft:red_terracotta",
            "minecraft:black_terracotta",
            "minecraft:white_glazed_terracotta",
            "minecraft:orange_glazed_terracotta",
            "minecraft:magenta_glazed_terracotta",
            "minecraft:light_blue_glazed_terracotta",
            "minecraft:yellow_glazed_terracotta",
            "minecraft:lime_glazed_terracotta",
            "minecraft:pink_glazed_terracotta",
            "minecraft:gray_glazed_terracotta",
            "minecraft:light_gray_glazed_terracotta",
            "minecraft:cyan_glazed_terracotta",
            "minecraft:purple_glazed_terracotta",
            "minecraft:blue_glazed_terracotta",
            "minecraft:brown_glazed_terracotta",
            "minecraft:green_glazed_terracotta",
            "minecraft:red_glazed_terracotta",
            "minecraft:black_glazed_terracotta",
            "minecraft:glass",
            "minecraft:glass_pane",
            "minecraft:tinted_glass",
            "minecraft:white_stained_glass",
            "minecraft:orange_stained_glass",
            "minecraft:magenta_stained_glass",
            "minecraft:light_blue_stained_glass",
            "minecraft:yellow_stained_glass",
            "minecraft:lime_stained_glass",
            "minecraft:pink_stained_glass",
            "minecraft:gray_stained_glass",
            "minecraft:light_gray_stained_glass",
            "minecraft:cyan_stained_glass",
            "minecraft:purple_stained_glass",
            "minecraft:blue_stained_glass",
            "minecraft:brown_stained_glass",
            "minecraft:green_stained_glass",
            "minecraft:red_stained_glass",
            "minecraft:black_stained_glass",
            "minecraft:white_stained_glass_pane",
            "minecraft:orange_stained_glass_pane",
            "minecraft:magenta_stained_glass_pane",
            "minecraft:light_blue_stained_glass_pane",
            "minecraft:yellow_stained_glass_pane",
            "minecraft:lime_stained_glass_pane",
            "minecraft:pink_stained_glass_pane",
            "minecraft:gray_stained_glass_pane",
            "minecraft:light_gray_stained_glass_pane",
            "minecraft:cyan_stained_glass_pane",
            "minecraft:purple_stained_glass_pane",
            "minecraft:blue_stained_glass_pane",
            "minecraft:brown_stained_glass_pane",
            "minecraft:green_stained_glass_pane",
            "minecraft:red_stained_glass_pane",
            "minecraft:black_stained_glass_pane",
            "minecraft:calcite",
            "minecraft:dripstone_block",
            "minecraft:amethyst_block",
            "minecraft:sea_lantern",
            "minecraft:glowstone",
            "minecraft:shroomlight",
            "minecraft:ochre_froglight",
            "minecraft:verdant_froglight",
            "minecraft:pearlescent_froglight",
            "minecraft:lantern",
            "minecraft:soul_lantern",
            "minecraft:end_rod",
            "minecraft:iron_bars",
            "minecraft:chain",
            "minecraft:bookshelf",
            "minecraft:chiseled_bookshelf",
            "minecraft:flower_pot",
            "minecraft:scaffolding",
            "minecraft:copper_block",
            "minecraft:exposed_copper",
            "minecraft:weathered_copper",
            "minecraft:oxidized_copper",
            "minecraft:waxed_copper_block",
            "minecraft:waxed_exposed_copper",
            "minecraft:waxed_weathered_copper",
            "minecraft:waxed_oxidized_copper",
            "minecraft:cut_copper",
            "minecraft:exposed_cut_copper",
            "minecraft:weathered_cut_copper",
            "minecraft:oxidized_cut_copper",
            "minecraft:waxed_cut_copper",
            "minecraft:waxed_exposed_cut_copper",
            "minecraft:waxed_weathered_cut_copper",
            "minecraft:waxed_oxidized_cut_copper",
            "minecraft:cut_copper_slab",
            "minecraft:exposed_cut_copper_slab",
            "minecraft:weathered_cut_copper_slab",
            "minecraft:oxidized_cut_copper_slab",
            "minecraft:waxed_cut_copper_slab",
            "minecraft:waxed_exposed_cut_copper_slab",
            "minecraft:waxed_weathered_cut_copper_slab",
            "minecraft:waxed_oxidized_cut_copper_slab",
            "minecraft:cut_copper_stairs",
            "minecraft:exposed_cut_copper_stairs",
            "minecraft:weathered_cut_copper_stairs",
            "minecraft:oxidized_cut_copper_stairs",
            "minecraft:waxed_cut_copper_stairs",
            "minecraft:waxed_exposed_cut_copper_stairs",
            "minecraft:waxed_weathered_cut_copper_stairs",
            "minecraft:waxed_oxidized_cut_copper_stairs",
            "minecraft:chiseled_copper",
            "minecraft:exposed_chiseled_copper",
            "minecraft:weathered_chiseled_copper",
            "minecraft:oxidized_chiseled_copper",
            "minecraft:waxed_chiseled_copper",
            "minecraft:waxed_exposed_chiseled_copper",
            "minecraft:waxed_weathered_chiseled_copper",
            "minecraft:waxed_oxidized_chiseled_copper",
            "minecraft:copper_grate",
            "minecraft:exposed_copper_grate",
            "minecraft:weathered_copper_grate",
            "minecraft:oxidized_copper_grate",
            "minecraft:waxed_copper_grate",
            "minecraft:waxed_exposed_copper_grate",
            "minecraft:waxed_weathered_copper_grate",
            "minecraft:waxed_oxidized_copper_grate",
            "minecraft:copper_door",
            "minecraft:exposed_copper_door",
            "minecraft:weathered_copper_door",
            "minecraft:oxidized_copper_door",
            "minecraft:waxed_copper_door",
            "minecraft:waxed_exposed_copper_door",
            "minecraft:waxed_weathered_copper_door",
            "minecraft:waxed_oxidized_copper_door",
            "minecraft:copper_trapdoor",
            "minecraft:exposed_copper_trapdoor",
            "minecraft:weathered_copper_trapdoor",
            "minecraft:oxidized_copper_trapdoor",
            "minecraft:waxed_copper_trapdoor",
            "minecraft:waxed_exposed_copper_trapdoor",
            "minecraft:waxed_weathered_copper_trapdoor",
            "minecraft:waxed_oxidized_copper_trapdoor",
        ]
        MINING_BLOCKS = [
            "minecraft:minecraft:stone",
            "minecraft:minecraft:granite",
            "minecraft:minecraft:diorite",
            "minecraft:minecraft:andesite",
            "minecraft:minecraft:deepslate",
            "minecraft:tuff",
            "minecraft:calcite",
            "minecraft:dripstone_block",
            "minecraft:cobblestone",
            "minecraft:cobbled_deepslate",
            "minecraft:coal_ore",
            "minecraft:deepslate_coal_ore",
            "minecraft:iron_ore",
            "minecraft:deepslate_iron_ore",
            "minecraft:copper_ore",
            "minecraft:deepslate_copper_ore",
            "minecraft:gold_ore",
            "minecraft:deepslate_gold_ore",
            "minecraft:redstone_ore",
            "minecraft:deepslate_redstone_ore",
            "minecraft:lapis_ore",
            "minecraft:deepslate_lapis_ore",
            "minecraft:diamond_ore",
            "minecraft:deepslate_diamond_ore",
            "minecraft:emerald_ore",
            "minecraft:deepslate_emerald_ore",
            "minecraft:nether_gold_ore",
            "minecraft:nether_quartz_ore",
            "minecraft:ancient_debris",
            "minecraft:netherrack",
            "minecraft:basalt",
            "minecraft:smooth_basalt",
            "minecraft:blackstone",
            "minecraft:end_stone",
            "minecraft:obsidian",
            "minecraft:crying_obsidian",
            "minecraft:amethyst_block",
            "minecraft:budding_amethyst",
            "minecraft:magma_block",
            "minecraft:clay",
            "minecraft:gravel"
        ]
        SILK_ORES = [
            "minecraft:coal_ore",
            "minecraft:deepslate_coal_ore",
            "minecraft:iron_ore",
            "minecraft:deepslate_iron_ore",
            "minecraft:copper_ore",
            "minecraft:deepslate_copper_ore",
            "minecraft:gold_ore",
            "minecraft:deepslate_gold_ore",
            "minecraft:redstone_ore",
            "minecraft:deepslate_redstone_ore",
            "minecraft:lapis_ore",
            "minecraft:deepslate_lapis_ore",
            "minecraft:diamond_ore",
            "minecraft:deepslate_diamond_ore",
            "minecraft:emerald_ore",
            "minecraft:deepslate_emerald_ore",
            "minecraft:nether_gold_ore",
            "minecraft:nether_quartz_ore",
        ]
        FARMING_ITEMS = [
            "minecraft:wheat",
            "minecraft:wheat_seeds",
            "minecraft:carrots",
            "minecraft:potatoes",
            "minecraft:beetroots",
            "minecraft:beetroot_seeds",
            "minecraft:melon",
            "minecraft:melon_slice",
            "minecraft:melon_seeds",
            "minecraft:pumpkin",
            "minecraft:pumpkin_seeds",
            "minecraft:sugar_cane",
            "minecraft:cactus",
            "minecraft:bamboo",
            "minecraft:cocoa_beans",
            "minecraft:nether_wart",
            "minecraft:sweet_berries",
            "minecraft:glow_berries",
            "minecraft:kelp",
            "minecraft:dried_kelp",
            "minecraft:brown_mushroom",
            "minecraft:red_mushroom",
            "minecraft:chorus_fruit",
            "minecraft:chorus_plant",
            "minecraft:chorus_flower",
            "minecraft:apple",
            "minecraft:hay_block",
            "minecraft:bone_meal",
            "minecraft:cocoa",
            "minecraft:bee_nest",
            "minecraft:beehive",
            "minecraft:honeycomb",
            "minecraft:honey_bottle",
            "minecraft:egg",
            "minecraft:milk_bucket",
            "minecraft:leather",
            "minecraft:feather",
            "minecraft:rabbit_hide",
            "minecraft:rabbit_foot",
            "minecraft:beef",
            "minecraft:porkchop",
            "minecraft:mutton",
            "minecraft:chicken",
            "minecraft:rabbit",
            "minecraft:cod",
            "minecraft:salmon",
            "minecraft:tropical_fish",
            "minecraft:pufferfish"
        ]

        mining_index = sum(stats.get("minecraft:mined", {}).get(block, 0) for block in MINING_BLOCKS) - sum(stats.get("minecraft:used", {}).get(block, 0) for block in SILK_ORES)
        building_index = sum(stats.get("minecraft:used", {}).get(block, 0) for block in BUILDING_BLOCKS)
        farming_index = sum(stats.get("minecraft:picked_up", {}).get(block, 0) for block in FARMING_ITEMS) + stats["minecraft:custom"].get("minecraft:animals_bred", 0)
        combat_index = stats.get("minecraft:custom", {}).get("minecraft:mob_kills", 0)
        redstone_index = sum(stats.get("minecraft:used", {}).get(block, 0) for block in REDSTONE_COMPONENTS)

        values = np.array([mining_index, building_index, farming_index, combat_index, redstone_index])

        values = values/(stats.get("minecraft:custom", {}).get('minecraft:play_time', 0)/(20*60*60))

        midpoints = np.array([
            500,
            250,
            100,
            20,
            50,
        ])

        norm_values = normalize(values, midpoints)

        labels = np.array(["Mining", "Building", "Farming", "Combat", "Redstone"])

        return norm_values, labels

    def new_page(self):
        self.canvas.showPage()
        self.canvas.setPageSize(A4)

    def save(self):
        try:
            self.canvas.save()
        except:
            raise ValueError("Cannot save file! Check if the output folder exists and is spelled correctly.")

def normalize(x, midpoints):
    x = np.asarray(x, dtype=float)
    midpoints = np.asarray(midpoints, dtype=float)

    x = np.maximum(x, 0)

    return 100 * x / (x + midpoints)

def get_main_travel(stats):
    custom = stats.get("minecraft:custom", {})

    travel_methods = {
        "Walking": (
            custom.get("minecraft:walk_one_cm", 0)
            + custom.get("minecraft:sprint_one_cm", 0)
            + custom.get("minecraft:crouch_one_cm", 0)
        ),
        "Elytra": custom.get("minecraft:aviate_one_cm", 0),
        "Boat": custom.get("minecraft:boat_one_cm", 0),
        "Horse": custom.get("minecraft:horse_one_cm", 0),
        "Minecart": custom.get("minecraft:minecart_one_cm", 0),
        "Swimming": custom.get("minecraft:swim_one_cm", 0),
        "Pig": custom.get("minecraft:pig_one_cm", 0),
        "Strider": custom.get("minecraft:strider_one_cm", 0),
    }

    return max(travel_methods, key=travel_methods.get) # type: ignore

def get_uuids(worldname):
    uuids = os.listdir(f'{worldname}/players/stats')
    return [id[:-5] for id in uuids]

def uuid_to_name(uuid):
    try:
        response = requests.get(f'https://api.minecraftservices.com/minecraft/profile/lookup/{uuid}')
    except:
        raise SystemError("Something went wrong! Please try again later or contact the creator.")
    if response.status_code == 200:
        data = response.json()
        name = data.get("name", "")
        return name
    else:
        return None

def remove_none_from_list(arr):
    return [x for x in arr if x is not None]

def select_name(names):
    if len(names) == 0:
        raise ValueError("No Player ever joined this World before.")
    for player in enumerate(names):
        print(f'({player[0]+1}) {player[1]}')
    option = input("Select a player: ")
    option = int(option)
    if option in range(1, len(names) + 1):
        return option - 1
    else:
        raise ValueError("Please select the player with the number next to their name.")

def get_head(uuid):
    response = requests.get(f'https://api.mcheads.org/head/{uuid}/256')
    if response.status_code == 200 and response:
        data = response.content
        return data
    else:
        with open("fallback.png", "rb") as file:
            return file.read()

def get_stats(filename):
    try:
        with open(filename) as f:
            data = f.read()
            data = json.loads(data)
            stats = data.get('stats', {})
            return stats
    except:
        raise ValueError("Can't open file.")

def get_advancement_stats(filename):
    try:
        with open(filename) as f:
            data = f.read()
            data = json.loads(data)
            stats = data
            return stats
    except:
        raise ValueError("Can't open file.")

USED_ITEMS = [
    # Tools
    "minecraft:wooden_shovel",
    "minecraft:wooden_pickaxe",
    "minecraft:wooden_axe",
    "minecraft:wooden_hoe",
    "minecraft:copper_shovel",
    "minecraft:copper_pickaxe",
    "minecraft:copper_axe",
    "minecraft:copper_hoe",
    "minecraft:stone_shovel",
    "minecraft:stone_pickaxe",
    "minecraft:stone_axe",
    "minecraft:stone_hoe",
    "minecraft:golden_shovel",
    "minecraft:golden_pickaxe",
    "minecraft:golden_axe",
    "minecraft:golden_hoe",
    "minecraft:iron_shovel",
    "minecraft:iron_pickaxe",
    "minecraft:iron_axe",
    "minecraft:iron_hoe",
    "minecraft:diamond_shovel",
    "minecraft:diamond_pickaxe",
    "minecraft:diamond_axe",
    "minecraft:diamond_hoe",
    "minecraft:netherite_shovel",
    "minecraft:netherite_pickaxe",
    "minecraft:netherite_axe",
    "minecraft:netherite_hoe"
    "minecraft:shears",
    "minecraft:flint_and_steel",
    "minecraft:fishing_rod",
    "minecraft:brush"
    # Weapons
    "minecraft:wooden_sword",
    "minecraft:copper_sword",
    "minecraft:stone_sword",
    "minecraft:golden_sword",
    "minecraft:iron_sword",
    "minecraft:diamond_sword",
    "minecraft:netherite_sword"
    "minecraft:wooden_spear",
    "minecraft:copper_spear",
    "minecraft:stone_spear",
    "minecraft:golden_spear",
    "minecraft:iron_spear",
    "minecraft:diamond_spear",
    "minecraft:netherite_spear"
    "minecraft:bow",
    "minecraft:crossbow",
    "minecraft:trident",
    "minecraft:mace"
    # Buckets
    "minecraft:bucket",
    "minecraft:water_bucket",
    "minecraft:lava_bucket",
    "minecraft:powder_snow_bucket",
    "minecraft:milk_bucket",
    "minecraft:cod_bucket",
    "minecraft:salmon_bucket",
    "minecraft:pufferfish_bucket",
    "minecraft:tropical_fish_bucket",
    "minecraft:axolotl_bucket",
    "minecraft:tadpole_bucket",
    "minecraft:sulfur_cube_bucket"
    # Utility
    "minecraft:carrot_on_a_stick",
    "minecraft:warped_fungus_on_a_stick",
    "minecraft:spyglass",
    "minecraft:goat_horn",
    "minecraft:ender_pearl",
    "minecraft:ender_eye",
    "minecraft:firework_rocket",
    "minecraft:fire_charge",
    "minecraft:wind_charge",
    "minecraft:experience_bottle",
    "minecraft:glass_bottle",
    "minecraft:lead",
    "minecraft:name_tag"
    # Throwable / ranged consumables
    "minecraft:snowball",
    "minecraft:egg",
    "minecraft:blue_egg",
    "minecraft:brown_egg",
    "minecraft:splash_potion",
    "minecraft:lingering_potion"
    # Storage / interactive items
    "minecraft:bundle",
    "minecraft:white_bundle",
    "minecraft:orange_bundle",
    "minecraft:magenta_bundle",
    "minecraft:light_blue_bundle",
    "minecraft:yellow_bundle",
    "minecraft:lime_bundle",
    "minecraft:pink_bundle",
    "minecraft:gray_bundle",
    "minecraft:light_gray_bundle",
    "minecraft:cyan_bundle",
    "minecraft:purple_bundle",
    "minecraft:blue_bundle",
    "minecraft:brown_bundle",
    "minecraft:green_bundle",
    "minecraft:red_bundle",
    "minecraft:black_bundle"
    # Farming / item actions
    "minecraft:bone_meal",
    "minecraft:white_dye",
    "minecraft:orange_dye",
    "minecraft:magenta_dye",
    "minecraft:light_blue_dye",
    "minecraft:yellow_dye",
    "minecraft:lime_dye",
    "minecraft:pink_dye",
    "minecraft:gray_dye",
    "minecraft:light_gray_dye",
    "minecraft:cyan_dye",
    "minecraft:purple_dye",
    "minecraft:blue_dye",
    "minecraft:brown_dye",
    "minecraft:green_dye",
    "minecraft:red_dye",
    "minecraft:black_dye",
]

def main():
    args = parser.parse_args()

    pdfmetrics.registerFont(TTFont("Arial", "ARIAL.TTF"))

    if not re.match(r"^.+/$", args.file):
        raise ValueError("Please use the Path, where your output file should go.")

    uuids = get_uuids(args.world_name)
    names = [uuid_to_name(id) for id in uuids]
    names = remove_none_from_list(names)
    selected_name = select_name(names)
    name = names[selected_name]
    uuid = uuids[selected_name]
    head = get_head(uuid)
    stats = get_stats(f"{args.world_name}/players/stats/{uuid}.json")
    advancement_stats = get_advancement_stats(f"{args.world_name}/players/advancements/{uuid}.json")
    pdf = PDFReport(args.file, args.name, name, args.world_name)
    radar_data = pdf.get_radar_chart_data(stats)
    pdf.add_header("Player Overview")
    pdf.add_stat_info(name, args.world_name, head, datetime.datetime.now())
    pdf.add_border(1/4)
    pdf.add_kpi_overview(stats)
    pdf.add_border(2/4)
    pdf.add_divider(1/6, 1/2)
    pdf.add_border(5/6)
    pdf.add_radar_chart(radar_data)
    pdf.add_highlight_stats(stats, USED_ITEMS)
    pdf.add_fun_fact(stats)
    pdf.new_page()
    pdf.add_border((1/2)/(A4[1]/A4[0]))
    pdf.add_divider(1-1/(A4[1]/A4[0]),1)
    pdf.add_border((1)/(A4[1]/A4[0]))
    pdf.add_mined_chart(stats)
    pdf.add_placed_chart(stats, USED_ITEMS)
    pdf.add_ore_chart(stats)
    pdf.add_killed_chart(stats)
    pdf.add_advancement_chart(advancement_stats)
    pdf.save()

if __name__ == "__main__":
    main()