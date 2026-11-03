# MineStats

#### Video Demo: [Video](https://youtu.be/8M7_ZhhkLso)

#### Description:

MineStats is a Python program that analyzes statistics from a Minecraft Java Edition world and turns them into a visual two-page PDF report.

Minecraft already has a built-in statistics screen where players can view information such as playtime, distance travelled, blocks mined, items used, mobs killed, deaths, and many other values. However, the vanilla statistics screen mostly presents this information as long lists of individual numbers. This is useful when looking for one specific statistic, but it is not very effective for understanding a player's overall behavior or playstyle.

MineStats takes a different approach. It reads the underlying Minecraft statistics and advancement data, selects relevant values, groups related statistics, performs additional calculations, and presents the results using charts and summaries. The goal is not to replace Minecraft's statistics system, but to make the information easier to understand and more visually interesting.

## How it works

Minecraft Java Edition stores player statistics in JSON files. These files contain categories such as `minecraft:mined`, `minecraft:used`, `minecraft:crafted`, `minecraft:killed`, and `minecraft:killed_by`.

MineStats reads these files and extracts the values needed for the report. Individual blocks and items are grouped into broader categories such as mining, building, Redstone, combat, and farming.

For example, mining includes blocks such as stone, deepslate, ores, and other underground materials. Redstone contains technical components such as repeaters, comparators, pistons, observers, and hoppers. Similar lists are used for the other activity categories.

These values are then used to calculate a playstyle profile. Since different Minecraft activities naturally produce very different numbers, the raw values cannot simply be compared directly. A player may mine tens of thousands of blocks while only placing a few hundred Redstone components. MineStats therefore normalizes the activity values before displaying them together in a radar chart.

The radar chart represents the player's relative playstyle rather than their skill. A high mining value means mining is a major part of that player's activity in the world, not that they are objectively better at mining.

## The PDF report

The final output is a two-page PDF report.

The first page is designed as an overview. It displays the player's Minecraft head, the world being analyzed, important overall statistics, and the playstyle radar chart.

It also includes interesting facts selected from the player's data. Instead of simply showing random statistics, the program compares several possible facts and tries to choose ones that are more notable or representative of the player.

The second page focuses more on detailed visualizations. It includes charts such as the player's most mined blocks, ore distribution, mob kills, and other activity statistics.

One visualization also uses biome exploration data. Minecraft's normal statistics are mostly cumulative counters, meaning they show how often something happened but usually not when it happened. Advancement data can contain timestamps, however. MineStats uses biome discovery timestamps to show exploration progress over time.

The biome discoveries are sorted chronologically and converted into a cumulative chart showing how many different biomes had been discovered at each point in time.

I decided to limit the report to two pages because I wanted it to remain compact. I considered creating separate pages for mining, building, Redstone, combat, and farming, but that would have made the report unnecessarily long. A two-page dashboard gives a quick overview while still including detailed statistics.

## Project files

### `project.py`

`project.py` contains the main implementation of MineStats.

It includes the `main` function and the functions used to read Minecraft data, calculate statistics, normalize values, create charts, and generate the PDF report.

It also contains the lists of blocks and items used to classify different activities. These lists allow the program to combine many individual Minecraft statistics into broader categories.

Matplotlib is used inside the program to create visualizations such as bar charts, the radar chart, and the biome exploration chart.

The PDF-generation code is also contained in `project.py`. It controls the positioning of headings, statistics, player information, images, and charts on the two report pages.

Although much of the project is stored in one file, the program is divided into separate functions and classes so that individual calculations can still be tested independently.

### `test_project.py`

`test_project.py` contains the automated tests for important functions from `project.py`.

The tests focus mainly on calculations and data-processing functions where the expected output can be clearly defined.

Visual elements such as the exact PDF layout are harder to test automatically, so the underlying values used by those visualizations are tested instead.

The tests are run using `pytest app.py`.

## Design decisions

One of the biggest design decisions was deciding what MineStats should provide that Minecraft's existing statistics screen does not.

I did not want to simply copy the game's statistics into another list. Instead, MineStats focuses on grouping, comparing, and visualizing the data.

For example, Minecraft may separately record how much stone, deepslate, coal ore, iron ore, and diamond ore the player has mined. MineStats can turn those individual counters into a ranked mining chart and an ore distribution chart.

Another challenge was normalization. Different activity categories use completely different scales, so directly comparing their totals would create a misleading radar chart. The program therefore transforms the category values before displaying them together.

I also had to decide which blocks and items should belong to each category. Some items can be used for several purposes, so not every classification is completely objective. I chose items that I felt best represented the activity being measured while avoiding common blocks that could distort the results.

The visual design was another important part of the project. I wanted the report to clearly feel connected to Minecraft without simply recreating Minecraft's interface. For this reason, I combined Minecraft elements such as the player head and block names with a cleaner data-analysis style.

## Challenges

One challenge was dealing with missing statistics. Minecraft does not necessarily store an entry for every possible block, item, or mob. If a player has never performed a certain action, the corresponding value may not exist in the JSON file.

The program therefore needs to safely handle missing dictionary values and interpret them as zero rather than causing an error.

Another challenge was working with the different structures used by Minecraft statistics and advancements. Statistics mainly contain counters, while advancement criteria can contain timestamps. Understanding these differences was important when deciding which visualizations were valid.

Generating the PDF also required careful layout planning. Unlike a terminal program, each element has to fit into a fixed page size, including text, charts, headings, and player information.

## Conclusion

MineStats takes Minecraft's large collection of individual statistics and converts them into a compact visual report.

The project combines several concepts from CS50's Introduction to Programming with Python, including file handling, JSON data, dictionaries, functions, testing, exception handling, and external libraries.

It also allowed me to explore additional areas such as data visualization, normalization, chart design, and automated PDF generation.

The result is a program that makes Minecraft statistics easier to interpret and gives the player a clearer picture of how they have spent their time in a particular world.