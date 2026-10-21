# Oneflood
OneFlood aims to facilitate the access to satellite-dervied surface water extent products, as well as develop a unique synthesis flood product (OneFlood) that combines products depending on their availability and cloud cover.

**Please note this package is in the early development stages and does not yet support full command line functionality**

# Installation 

## Step 1: Download the Source Code

```bash
git clone https://github.com/mickymags/oneflood.git
```

## Step 2: Installation

We have provided multiple ways to install OneFlood to ensure interoperability between operating systems 

**Step 2 Option 1: YAML file**

Run the below code after running the code in Step 1 
```bash
cd oneflood
conda install -f oneflood_env.yaml
conda activate oneflood
```
This may take some time (and appear to be stalling on the Solving environment step). 
For a faster download, consider using mamba rather than conda. 

**Step 2 Option 2: Install using Pixi (IN PROGRESS)**
Pixi allows for a reproducible environment that shares interoperability between operating systems. This package was developed on a Linux machine so this option is recommended if you are on Mac or Windows. 

```bash
pixi install 
pixi run oneflood --help
```

**Step 2 Option 3: Install Using PyPI (IN PROGRESS)** 

By the launch of OneFlood Version 1, we hope to make oneflood available via the Python Package Index


## Step 3: Usage (IN PROGRESS)

OneFlood supports the command-line usage, supporting several functions 

**Step 3a: product_availability function

```bash
oneflood product_availability --aoi xmin ymin xmax ymax --date_of_int 2026-10-15
```

This method will provide you with the overpass dates and times of flood products for a region of interest. 






