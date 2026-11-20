"""Storage physics regressions without loading the plotting/ML dependencies."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "microgridRLsimulator"


def load_storage():
    packages = {}
    for name, directory in [("microgridRLsimulator", ROOT), ("microgridRLsimulator.model", ROOT / "model")]:
        module = ModuleType(name)
        module.__path__ = [str(directory)]
        packages[name] = module
    with patch.dict(sys.modules, packages):
        loaded = {}
        for suffix, file in [("model.device", "model/device.py"), ("utils", "utils.py"), ("model.storage", "model/storage.py")]:
            name = "microgridRLsimulator." + suffix
            spec = importlib.util.spec_from_file_location(name, ROOT / file)
            module = importlib.util.module_from_spec(spec)
            loaded[name] = module
            with patch.dict(sys.modules, loaded):
                spec.loader.exec_module(module)
        return loaded["microgridRLsimulator.model.storage"].Storage


Storage = load_storage()


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.storage = Storage("battery", dict(capacity=10, max_charge_rate=5,
            max_discharge_rate=5, charge_efficiency=0.8, discharge_efficiency=0.8))

    def test_opposing_commands_use_net_power(self):
        self.assertEqual(self.storage.actual_power(3, 1), (2, 0))
        self.assertEqual(self.storage.actual_power(1, 3), (0, 2))

    def test_balanced_commands_do_not_charge_or_discharge(self):
        for charge, discharge in [(2, 2), (2.01, 2), (2, 2.01)]:
            with self.subTest(charge=charge, discharge=discharge):
                self.assertEqual(self.storage.simulate(5, charge, discharge), (5, 0, 0))

    def test_charge_respects_capacity_and_efficiency(self):
        self.assertEqual(self.storage.simulate(9, 3, 0), (10, 1.25, 0))

    def test_discharge_respects_empty_boundary_and_efficiency(self):
        self.assertEqual(self.storage.simulate(1, 0, 3), (0, 0, 0.8))


if __name__ == "__main__":
    unittest.main()
