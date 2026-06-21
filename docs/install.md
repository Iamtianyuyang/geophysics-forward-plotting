# Installation Guide

## Option 1: conda (recommended)

```bash
conda env create -f environment.yml
conda activate geophysics-forward-plotting
```

**Note for China users:** If conda is slow, use the Tsinghua mirror:
```bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes
```

Or use mamba for faster solving:
```bash
conda install -n base -c conda-forge mamba
mamba env create -f environment.yml
```

## Option 2: pip (minimal, no conda required)

```bash
pip install -e ".[plot,dev]"
```

This installs: numpy, pyyaml, matplotlib, pytest, ruff.

## Option 3: Add matplotlib to existing conda env

If the conda env was created without matplotlib (old environment.yml):
```bash
conda activate geophysics-forward-plotting
conda install matplotlib -c conda-forge
```

## Verify installation

```bash
conda activate geophysics-forward-plotting
python -c "from geophysics_forward_plotting import PlottingAgent; print(PlottingAgent().available_skills())"
gfp skills
```

## Run tests

```bash
pytest tests/ -v
```

## Generate example data and run a demo

```bash
gfp data examples/data
python examples/scripts/demo_velocity_model.py
python examples/scripts/demo_compare_4methods.py
```
