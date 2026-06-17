import pybullet as p
import pybullet_data
import time

# 1. Inicjalizacja symulatora z widokiem GUI
physicsClient = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# 2. Ustawienie grawitacji i podłoża
p.setGravity(0, 0, -9.81)
planeId = p.loadURDF("plane.urdf")

# 3. Wczytanie modelu Unitree Go1 (używamy stabilnego repozytorium open-source)
# PyBullet potrafi pobierać pliki bezpośrednio z URL, jeśli podasz pełną ścieżkę do surowego pliku GitHub!
urdf_url = "https://raw.githubusercontent.com/unitreerobotics/unitree_ros/master/robots/go1_description/urdf/go1.urdf"

# Ustalamy pozycję startową, żeby pies nie wpadł pod ziemię
robotStartPos = [0, 0, 0.4] 
robotStartOrientation = p.getQuaternionFromEuler([0, 0, 0])

print("Pobieranie i wczytywanie modelu Unitree Go1...")
try:
    # Wczytujemy robota. UWAGA: Może minąć kilka sekund, zanim pobiorą się pliki 3D (.dae/.stl)
    go1_id = p.loadURDF(urdf_url, robotStartPos, robotStartOrientation, useFixedBase=False)
    print("Unitree Go1 wczytany pomyślnie!")
except Exception as e:
    print("Błąd wczytywania z sieci. Możesz też pobrać folder 'go1_description' lokalnie na dysk.", e)
    exit()

# 4. Pętla symulacji
while True:
    p.stepSimulation()
    time.sleep(1./240.)