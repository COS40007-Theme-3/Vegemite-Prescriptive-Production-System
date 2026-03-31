import json
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)
d = '{"part": "Yeast - BRN", "ffteFeedSolidsSP": 50, "ffteProductionSolidsSP": 41.5, "ffteSteamPressureSP": 123.0, "tfeOutFlowSP": 2038.5, "tfeProductionSolidsSP": 65.0, "tfeVacuumPressureSP": -79.9, "tfeSteamPressureSP": 120.0}'
import subprocess
print(subprocess.check_output(['python3', 'models/serve_recommend_sp.py'], input=d.encode()).decode())
