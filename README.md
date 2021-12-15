# GrowF
![Banner](https://user-images.githubusercontent.com/1012779/144693909-a46458a3-2b72-4e3c-84ed-038187e7eac6.png)

Grow Function: Generate 3D Stacked Bifurcating Double Deep Cellular Automata based organisms which differentiate using a Genetic Algorithm... 

TLDR; High Def Living Trees that you can breed, trim and mint as NFTs on Solana, Ethereum, Cardano and other blockchain networks.

This demo represents the current state of the codebase.  If anyone wishes to join this project, please contact or fork.

Written in Python using the Blender Library

Current state of development https://www.youtube.com/watch?v=R8qGZmVQ0rU

## Installation
* Install Blender if you don't already have it
* Open treegen.blend

Once opened, you can generate whatever tree is currently there by default by going to the scripting tab, opening tree.py and pressing the Run button

![Banner2](https://user-images.githubusercontent.com/1012779/144967405-9696e42b-45a9-45ac-90e8-0b153df6ccc4.png)

## We Have the Technology

Recent developments in the fields of Cellular Automata and Genetic Algorithms have led to the possibility of growing living organisms in higher dimensions.  Many projects like Lenia, The Life Engine and even VR games like Playne, and Inward have made a big deal of living organisms in games and tech culture.  These living organisms can behave like bacteria, like larger soft-bodied oganisms, or like Trees.  On a scientific level, there exist virtual living ecosystems of over 500,000 plants in simulations like the ones seen in the paper "[Synthetic Silviculture: Multi-Scale Modeling of Plant Ecosystems](https://storage.googleapis.com/pirk.io/projects/synthetic_silviculture/index.html)". These multi-scale simulations are focused on larger scale dynamics, creating realistic, yet estimated details, (albeit through rigorous scientific analysis to approximate reality). 

But that begs the question, how high definition can we go in creating growing 3D systems?  Can cell differentiation be accquired by genetic algorithm in new and spontaneous ways which account for ecosystem? This project aims to advance toward answering those questions, starting with what we think will end up being hi-res tree models, but could end up as anything.

I think it's also possible to go to infinite resolution by making a growth protocol that is forward compatible, so that the computers of the future which operate on orders of magnitude of higher parallelism can show the same tree you minted in 2022, in much higher detail.

## How does the GrowF Algorithm Work?

Like many mathematical creations, GrowF stands on the shoulders of concepts created by others.  For instance, the Boids algorithm is a cellular automata (artificial life) algorithm that originally made CAs popular.  Right now GrowF only uses three cellular automata cell types:

* Tips
* Slices
* Radial Cells

Tips can bifurcate creating new Tips according to DNAs instruction set.  Tips technically travel through space in this algorithm by themselves.  They have two major forces that affect them, which are photolocation and geolocation.  One pulls it toward the light (simulating how tips seek light), one causes it to bend away from gravity.  This is simulated by lerping the velocity vector of the tip slightly toward these two vectors.  Each tip has it's own account of where light and where gravity is.  A Tip can be one of two sub-classes: Roots an Shoots.  Right now GrowF is only showing shoots, but roots will be added soon.  

Slices are a center cell and a generate a number of radial cells laid down in a circular slice perpendicular to the Tip's growth direction.  Currently, slices do not have a growth function, they only serve as a center point for radial cells.

Radial Cells are laid down radially on each slice of each tip, forming the surface structure of branches, leaves, flowers, buds, and whatever other shape that can be created by the GrowF algorithm. The slice cell lays down the radial cells using specific curves over the series.  Radial cells have other radial cells as neighbors (a linking kernel is used on the slice), as well as being linked to the cell directly "above" them mutually, being affected by them and affecting them via "boids" like rules.

![Param_plin_branch_13](https://user-images.githubusercontent.com/1012779/145695569-194ff996-34f2-44dc-8eee-79568c1db41e.png)

## Parameters

Recently, I have created a "Param" class that acts as a value which is static, or can be dynamic.  This means that there is now the possibility of cell differentiation. The dynamic functions of parameters are usually infinite sets or repeating finite sets of numbers which represent future possible values of the parameter.  Parameters are now set up inside the DNA of each cell.  Each parameter has a "next" function which can be called for instance on bifurcation, or each cell step, etc., allowing every aspect of each cell to have some sort of progression over it's life span, controlling things like the cell's growth coeficient or it's initial placement.  Now parameters are part of the core functionality of the algorithm, allowing a function or set of functions to define the values of any aspect of growth over time.

## Features of GrowF Virtual Organisms

* Parameter based organism life arc design (designer DNA)
* Genetic Algorithm based design (organic DNA)
* Namespaces give organisms a "Multiverse effect"
* Evolution controlled cell nucleus Neural Networks (TBA)
* Cell differentiation over time and space
* All organisms are fully destructable (all parts/organs can be removed after growth)

## Hormones and Chemical Messaging between Cells

TBA

## The Metaverse Needs Life: The Future of GrowF

Part of why I started GrowF was inspired by the idea of the many metaverses that are possible because of VR and blockchain.  Those games need lots of assets to populate entire worlds.  For me, it is hard to model trees that are realistic in any 3D modeling platform.  Much less, make them lowpoly or high poly, or ready for video games or kinematics and physics. But if you think about it, it's hard to make believable trees because trees are grown, not sculpted by nature. They are the results of a bunch of growth patterns that came together to form what we categorize as trees or even any type of plant.  The bifurcation structure of a tree is everywhere.  You needen't go as far as looking at the human nervous system, or in the structure of folders in your computer, to see that same tree organization.  Imagine having a tree that you can plant on top of a structure like a stone sculpture in VR and watch it's roots eating through the walls and stone in hyper-real time.  Imagine breeding trees to be a specific color or give a specific type of fruit, or growing them in zero gravity.  Imagine planting a garden and watching your plants and trees grow together over time and generations.

## NFTs

Living virtual organisms grown with GrowF are unique.  The 3D Models of their life progression can be included in games using Non-Fungible Tokens (NFTs).  If you can own any unique digital item, why not own a tree that you have bred, or trimmed, or simply that you found in a VR game somewhere.  Think about trimming, or when trees bear fruits that have specific properties or visual peculiarities.  Each branch of the tree can be removed, the fruits or leaves, (or whatever ends up growing on a bifurcation) can be separated from the tree, recorded as removed in the tree's history (affecting it's model forever).  Just like with real trees, the seeds in those fruits can be minted and given to friends or sold, reflecting the value that you have added to the tree by planting and growing it somewhere in the Metaverse.  It could end up seeding virtual forests, or being used as CG set pieces in movies or video games depending on who buys it from you.

## So, You are a Crafter?

![destructable](https://user-images.githubusercontent.com/1012779/146231113-7a7ecd6a-49ef-4843-8180-a4dd39cd13a2.png)

Everything grown with GrowF has differentiated parts or organs that you can use seperately.  You can pick flowers, stems, leaves, or anything that grows for you, and use them as part of something else, or as a standalone mesh/model.
