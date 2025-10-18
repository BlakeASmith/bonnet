bonnet topic "The Meaning of Life" -t thought,question --id M1
bonnet topic "Another topic"  # ID will be auto-generated

bonnet fact "Answer=42" --about M1

bonnet ref "The hitchhikers guide to the galaxy" --id R1

> bonnet context --about M1
<context>
M1:"The meaning of life"
R1:"The Hitchhikers Guide to the Galaxy"
Fact:M1:Answer=42
Ref:M1:R1
<context>

