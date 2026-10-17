# Synthetic transfer exercise

This small model exercises development resources; it makes no empirical claim.
Use Python 3.12 and the dependencies below.
Run these commands from this model project's root, after copying the development
skill's `assets/run_output.py` into `transfer/run_output.py`:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install 'mesa[network]>=3.5,<3.6' 'pytest>=8,<10'
python -m pytest -q
python -m transfer --steps 6 --seed 41
```

Each model step activates five traders in random order. A trader with a positive
balance transfers one unit to a randomly selected other trader. The initial total
is 15 and is conserved. Observations include initialization and every completed
step. Each export uses a fresh `outputs/run-NNNN/observations.json` destination.
