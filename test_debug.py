import sys
sys.path.insert(0, r'C:\instrument-designer')
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

inst = tmm_instrument_from_radii(
    [7.25]*6, 300.0,
    [50, 90, 130, 170, 210, 250],
    [7.0]*6, [3.75]*6,
    22.0, closed_top=True, cone_step=0.5,
)

# C4 all closed
fing = ['closed']*6
print('All closed (C4 target):')
for wl in [1000, 1100, 1100, 1200, 1231, 1250, 1300]:
    phase = inst.resonance_phase(wl, ['closed']*6)
    f = SPEED_OF_SOUND / wl
    print(f'  wl={wl}: phase={phase:.4f}, f={SPEED_OF_SOUND/wl:.1f}Hz')

# C#4: fingering with hole 5 (index 5 = position 250mm from reed) open
# In chalumier coordinates: hole at 50mm from bell = index 5 in our array
print()
print('C#4 (hole 5 open = 250mm from reed = 50 from bell):')
fing = ['closed']*5 + ['open']
for wl in [1000, 1050, 1050, 1100, 1102, 1200]:
    phase = inst.resonance_phase(wl, ['closed']*5 + ['open'])
    f = SPEED_OF_SOUND / wl
    print(f'  wl={wl}: phase={phase:.4f}, f={SPEED_OF_SOUND/wl:.1f}Hz')

# Try true_wavelength_near
print()
print('true_wavelength_near for C#4 (target 277.2Hz = 1246mm):')
target_wl = 343200 / 277.2  # 1238mm
wl = inst.true_wavelength_near(1238*0.85, ['closed']*5 + ['open'])
print(f'  result: wl={wl:.0f}mm, f={343200/wl:.1f}Hz')

# Check register 2
print()
print('Register 2 for C#4:')
wl = inst.true_nth_wavelength_near(1238*0.85, ['closed']*5 + ['open'], n=2)
print(f'  n=2: wl={wl:.0f}mm, f={343200/wl:.1f}Hz')
print(f'  n=1: wl={inst.true_nth_wavelength_near(1000, ["closed"]*5 + ["open"], n=1):.0f}mm, f={343200/wl:.1f}Hz')