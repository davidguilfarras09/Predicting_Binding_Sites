load 4HHB.pdb, protein
select binding_A, chain A and resi 42+58+61+62+87+93
show sticks, binding_A
color red, binding_A
select binding_B, chain B and resi 41+42+67+92+98
show sticks, binding_B
color red, binding_B
select binding_site, binding_A or binding_B
zoom binding_site