from project import *
import numpy as np
from unittest.mock import Mock, mock_open, patch, call
import pytest

def test_zero_normalize():
    assert np.allclose(normalize([0, 0, 0, 0, 0], [500,250,100,20,50]), [0, 0, 0 ,0, 0])
    assert np.allclose(normalize([0, 0, 0, 0, 0], [1,100000,-50,2,9]), [0, 0, 0 ,0, 0])

def test_midpoint_normalize():
    assert np.allclose(normalize([1, 50, 20, 20, 10], [1,50,20,20,10]), [50, 50, 50, 50, 50])
    assert np.allclose(normalize([4, 100, 40, 40, 20], [1,25,10,10,5]), [80, 80, 80, 80, 80])

def test_get_main_travel():
    walking_stats = {
        "minecraft:custom": {
            "minecraft:walk_one_cm": 1000,
            "minecraft:sprint_one_cm": 500,
            "minecraft:crouch_one_cm": 200,
            "minecraft:aviate_one_cm": 100,
            "minecraft:boat_one_cm": 50,
            "minecraft:horse_one_cm": 20,
            "minecraft:minecart_one_cm": 10,
            "minecraft:swim_one_cm": 300,
            "minecraft:pig_one_cm": 0,
            "minecraft:strider_one_cm": 0,
        }
    }
    elytra_stats = {
        "minecraft:custom": {
            "minecraft:walk_one_cm": 100,
            "minecraft:sprint_one_cm": 100,
            "minecraft:crouch_one_cm": 0,
            "minecraft:aviate_one_cm": 5000,
            "minecraft:boat_one_cm": 200,
            "minecraft:horse_one_cm": 100,
            "minecraft:minecart_one_cm": 50,
            "minecraft:swim_one_cm": 300,
            "minecraft:pig_one_cm": 0,
            "minecraft:strider_one_cm": 0,
        }
    }
    boat_stats = {
        "minecraft:custom": {
            "minecraft:walk_one_cm": 100,
            "minecraft:sprint_one_cm": 200,
            "minecraft:crouch_one_cm": 50,
            "minecraft:aviate_one_cm": 500,
            "minecraft:boat_one_cm": 6000,
            "minecraft:horse_one_cm": 1000,
            "minecraft:minecart_one_cm": 400,
            "minecraft:swim_one_cm": 200,
            "minecraft:pig_one_cm": 0,
            "minecraft:strider_one_cm": 0,
        }
    }
    swimming_stats = {
        "minecraft:custom": {
            "minecraft:walk_one_cm": 100,
            "minecraft:sprint_one_cm": 100,
            "minecraft:crouch_one_cm": 0,
            "minecraft:aviate_one_cm": 200,
            "minecraft:boat_one_cm": 300,
            "minecraft:horse_one_cm": 100,
            "minecraft:minecart_one_cm": 50,
            "minecraft:swim_one_cm": 4000,
            "minecraft:pig_one_cm": 0,
            "minecraft:strider_one_cm": 0,
        }
    }
    empty_stats = {}
    assert get_main_travel(walking_stats) == "Walking"
    assert get_main_travel(elytra_stats) == "Elytra"
    assert get_main_travel(boat_stats) == "Boat"
    assert get_main_travel(swimming_stats) == "Swimming"
    assert get_main_travel(empty_stats) == "Walking"

def test_remove_none_from_list():
    assert remove_none_from_list(["Steve", None, "Alex", None]) == ["Steve", "Alex"]
    assert remove_none_from_list([None, None, None]) == []
    assert remove_none_from_list(["Steve", "Alex"]) == ["Steve", "Alex"]
    assert remove_none_from_list([]) == []
    assert remove_none_from_list([1, None, 2, None, 3]) == [1, 2, 3]
    assert remove_none_from_list(["", None, 0, False]) == ["", 0, False]

def test_get_uuids():
    with patch("project.os.listdir") as mock_listdir:
        mock_listdir.return_value = [
            "abc123.json",
            "def456.json"
        ]

        results = get_uuids("world")

        assert results == ["abc123", "def456"]

        mock_listdir.assert_called_once_with(
            "world/players/stats"
        )

def test_uuid_to_name_succes():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "name": "Steve"
    }

    with patch(
        "project.requests.get",
        return_value=response
    ): assert uuid_to_name("abc") == "Steve"

def test_uuid_to_name_not_found():
    response = Mock()
    response.status_code = 404

    with patch(
        "project.requests.get",
        return_value=response
    ): assert uuid_to_name("abc") is None

def test_uuid_to_name_network_error():
    with patch(
        "project.requests.get",
        side_effect=Exception()
    ):
        with pytest.raises(SystemError):
            uuid_to_name("abc")

def test_uuid_to_name_missing_name():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {}

    with patch(
        "project.requests.get",
        return_value=response
    ):
        assert uuid_to_name("abc") == ""

def test_get_head_success():
    response = Mock()
    response.status_code = 200
    response.content = b"image data"

    with patch(
        "project.requests.get",
        return_value=response
    ):
        assert get_head("abc") == b"image data"

def test_get_head_fallback():
    response = Mock()
    response.status_code = 404

    mocked_file = mock_open(
        read_data=b"fallback image"
    )

    with patch(
        "project.requests.get",
        return_value=response
    ):
        with patch(
            "builtins.open",
            mocked_file
        ):
            result = get_head("abc")

    assert result == b"fallback image"

def test_get_head_missing_fallback():
    response = Mock()
    response.status_code = 404

    with patch(
        "project.requests.get",
        return_value=response
    ):
        with patch(
            "builtins.open",
            side_effect=FileNotFoundError
        ):
            with pytest.raises(FileNotFoundError):
                get_head("abc")

def test_get_stats():
    data = """
    {
        "stats": {
            "minecraft:custom": {
                "minecraft:jump": 10
            }
        }
    }
    """

    with patch(
        "builtins.open",
        mock_open(read_data=data)
    ):
        result = get_stats("whatever.json")

    assert result == {
        "minecraft:custom": {
            "minecraft:jump": 10
        }
    }

def test_get_stats_missing_stats():
    with patch(
        "builtins.open",
        mock_open(read_data="{}")
    ):
        assert get_stats("test.json") == {}

def test_get_stats_invalid_json():
    with patch(
        "builtins.open",
        mock_open(read_data="not json")
    ):
        with pytest.raises(ValueError):
            get_stats("test.json")

def test_get_stats_missing_file():
    with patch(
        "builtins.open",
        side_effect=FileNotFoundError
    ):
        with pytest.raises(ValueError):
            get_stats("test.json")

def test_get_advancement_stats():
    data = """
    {
        "minecraft:story/root": {
            "done": true
        }
    }
    """

    with patch(
        "builtins.open",
        mock_open(read_data=data)
    ):
        result = get_advancement_stats("adv.json")

    assert result["minecraft:story/root"]["done"] is True

def test_get_advancement_stats_invalid():
    with patch(
        "builtins.open",
        mock_open(read_data="broken")
    ):
        with pytest.raises(ValueError):
            get_advancement_stats("adv.json")

def test_get_advancement_stats_missing():
    with patch(
        "builtins.open",
        side_effect=FileNotFoundError
    ):
        with pytest.raises(ValueError):
            get_advancement_stats("adv.json")

def test_pdf_init():
    fake_canvas = Mock()

    with patch(
        "project.canvas.Canvas",
        return_value=fake_canvas
    ):
        report = PDFReport(
            "./",
            "report",
            "Steve",
            "World"
        )

    assert report.canvas is fake_canvas
    assert report.player_name == "Steve"

def test_pdf_init_failure():
    with patch(
        "project.canvas.Canvas",
        side_effect=Exception()
    ):
        with pytest.raises(ValueError):
            PDFReport(
                "./",
                "report",
                "Steve",
                "World"
            )

def test_radar_values_not_1d():
    report = PDFReport.__new__(PDFReport)

    with pytest.raises(ValueError):
        report.add_radar_chart(
            (
                [[1, 2], [3, 4]],
                ["A", "B"]
            )
        )

def test_radar_different_lengths():
    report = PDFReport.__new__(PDFReport)

    with pytest.raises(ValueError):
        report.add_radar_chart(
            (
                [10, 20, 30],
                ["A", "B"]
            )
        )

def test_radar_valid():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    report.add_radar_chart(
        (
            [20, 40, 60, 80, 50],
            ["A", "B", "C", "D", "E"]
        )
    )

    report.canvas.drawImage.assert_called_once()

def test_radar_combat():
    report = PDFReport.__new__(PDFReport)

    stats = {
        "minecraft:custom": {
            "minecraft:play_time": 20 * 60 * 60,
            "minecraft:mob_kills": 20,
            "minecraft:animals_bred": 0,
        },
        "minecraft:mined": {},
        "minecraft:used": {},
        "minecraft:picked_up": {},
    }

    values, labels = report.get_radar_chart_data(stats)

    assert labels[3] == "Combat"
    assert values[3] == 50

def test_radar_calls_normalize():
    report = PDFReport.__new__(PDFReport)

    stats = {
        "minecraft:custom": {
            "minecraft:play_time": 72000,
            "minecraft:animals_bred": 0,
            "minecraft:mob_kills": 0,
        },
        "minecraft:mined": {},
        "minecraft:used": {},
        "minecraft:picked_up": {},
    }

    with patch(
        "project.normalize",
        return_value=np.array(
            [1, 2, 3, 4, 5]
        )
    ) as mock_normalize:

        result, _ = (
            report.get_radar_chart_data(stats)
        )

    mock_normalize.assert_called_once()

    assert np.array_equal(
        result,
        [1, 2, 3, 4, 5]
    )

def test_kpi_overview():
    report = PDFReport.__new__(PDFReport)
    report.add_kpi_stat = Mock()

    stats = {
        "minecraft:custom": {
            "minecraft:play_time": 72000,
            "minecraft:mob_kills": 10,
            "minecraft:deaths": 2,
            "minecraft:walk_one_cm": 100000,
        },
        "minecraft:mined": {
            "minecraft:stone": 100,
            "minecraft:dirt": 50,
        },
        "minecraft:crafted": {
            "minecraft:stick": 20
        }
    }

    report.add_kpi_overview(stats)

    calls = report.add_kpi_stat.call_args_list

    assert len(calls) == 6

def test_highlight_stats():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    stats = {
        "minecraft:mined": {
            "minecraft:stone": 100,
            "minecraft:diamond_ore": 5
        },
        "minecraft:used": {
            "minecraft:stone": 50,
            "minecraft:diamond_pickaxe": 300
        },
        "minecraft:killed": {
            "minecraft:zombie": 20
        },
        "minecraft:custom": {
            "minecraft:walk_one_cm": 1000
        }
    }

    report.add_highlight_stats(
        stats,
        []
    )

    written = [
        c.args[2]
        for c
        in report.canvas.drawString.call_args_list
    ]

    assert any(
        "Most Mined: Stone" in x
        for x in written
    )

    assert any(
        "Most Killed: Zombie" in x
        for x in written
    )

def test_fun_fact_mob_hunter():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    stats = {
        "minecraft:custom": {
            "minecraft:play_time": 72000,
            "minecraft:mob_kills": 50,
            "minecraft:jump": 10,
        }
    }

    report.add_fun_fact(stats)

    texts = [
        c.args[2]
        for c
        in report.canvas.drawCentredString.call_args_list
    ]

    assert "Mob Hunter" in texts

def test_fun_fact_zero_playtime():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    stats = {
        "minecraft:custom": {
            "minecraft:play_time": 0
        }
    }

    with pytest.raises(ZeroDivisionError):
        report.add_fun_fact(stats)

def test_add_mined_chart():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    stats = {
        "minecraft:mined": {
            "minecraft:stone": 500,
            "minecraft:dirt": 200,
        }
    }

    report.add_mined_chart(stats)

    report.canvas.drawImage.assert_called_once()

def test_add_header():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    report.add_header("Player Overview")

    report.canvas.drawString.assert_any_call(
        MARGIN,
        HEIGHT - 2 * MARGIN,
        "Minestats"
    )

    report.canvas.drawString.assert_any_call(
        MARGIN,
        HEIGHT - 3 * MARGIN,
        "Player Overview"
    )

def test_new_page():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    report.new_page()

    report.canvas.showPage.assert_called_once()

def test_save():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    report.save()

    report.canvas.save.assert_called_once()

def test_save_failure():
    report = PDFReport.__new__(PDFReport)
    report.canvas = Mock()

    report.canvas.save.side_effect = Exception()

    with pytest.raises(ValueError):
        report.save()

def test_main():
    fake_args = Mock(
        world_name="world",
        file="./",
        name="report"
    )

    fake_pdf = Mock()

    with patch(
        "project.parser.parse_args",
        return_value=fake_args
    ), patch(
        "project.get_uuids",
        return_value=["uuid123"]
    ), patch(
        "project.uuid_to_name",
        return_value="Steve"
    ), patch(
        "project.select_name",
        return_value=0
    ), patch(
        "project.get_head",
        return_value=b"image"
    ), patch(
        "project.get_stats",
        return_value={}
    ), patch(
        "project.get_advancement_stats",
        return_value={}
    ), patch(
        "project.PDFReport",
        return_value=fake_pdf
    ):

        fake_pdf.get_radar_chart_data.return_value = (
            [1, 2, 3, 4, 5],
            ["A", "B", "C", "D", "E"]
        )

        main()

    fake_pdf.save.assert_called_once()

def test_main_invalid_path():
    fake_args = Mock(
        world_name="world",
        file="output",
        name="report"
    )

    with patch(
        "project.parser.parse_args",
        return_value=fake_args
    ):
        with pytest.raises(ValueError):
            main()