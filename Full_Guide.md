
# Commands cheat sheet

```
**select** RollA **from** 1 to 6
**select** RollB **from** 1,2, 3 to 5 ,6
**select** RollC **from** 1,1,2,2,3,4,5,6
**select** RollD **from** 1 to 10 **where** RollD >= RollC
RollE = select(1 to 6) + select(3 to 4) + select(1 to select(1 to 6))

RollB = RollB + 1

if RollB > RollA
	print "This doesn't mean much, huh"
elif rollB < 3
	print 3/2
else
	print 1,2,3

bychance rollA != 3

input MyVar "Did you know you can get input?"
print MyVar

for i from 1 to rollD
	print i

# Ways to end a program:
pass
fail
done
return
return "hi"
return rollB + 3

```

# Sample code

What are the odds that sum of two dice is a 12:

```python3
select rollA from 1 to 6
select rollB from 1 to 6
if rollA + rollB == 12
	pass
else
	fail
```

Dependent probability: what are the odds that the sum of two dice is a 7, *GIVEN THAT* their sum is odd.

```python3
select rollA from 1 to 6
select rollB from 1 to 6
bychance (rollA + rollB) % 2 == 1
if rollA + rollB == 7
	pass
else
	fail
```

If you flip a coin 100 times, what are the odds you get exactly 50 heads:

```python3
total = 0
for i from 1 to 100
	total = total + select(0 to 1)
if total == 50
	pass
else
	fail
```

The monty hall problem:
```python3
# There are three doors
doors = 1,2,3
# One of them has a prize behind it.
select prize from doors
# A player is called up to the stage. They point at a door of their choosing.
select playerChoice from doors
# The host (who knows where the prize is), opens one of the other two doors to reveal that it is empty.
select hostOpened from doors where hostOpened != playerChoice and hostOpened != prize
# The player must now choose: do they open the door they originally picked, or the other one? They choose to switch.
select otherDoor from doors where otherDoor != hostOpened and otherDoor != playerChoice
# What are the odds that they get the prize?
if otherDoor != prize
	fail
pass # Note: 'pass' means 'succeed'. To do nothing, use 'nop' instead
```

# Select command:

```
**select** varname **from** listOrExpr

**select** varname **from** listOrExpr **where** conditionsUsingVarname

var = select(listOrExpr)
```

Select generates a random number from the list of options. Each option has an equal chance of occuring, but items can be included multiple times on the list. (For example, (1,1,2,3) has a 1/2 chance of being a 1)

The 'where' keyword allows for finer control. You can include conditions dependent on the variable you are defining, like:

```**select** rollA from 1 to 6 where rollA > 3```

An in-line select (```select(1 to 6)```) works the same way, but it can be included in a formula. It cannot contain a 'where' component, though. (It also affects how graphs are drawn, but that is found in the 'Graph' section of this document)

# If command

```
if roll == 6
	print "big!"
elif roll > 3
	print "medium"
elif roll == 3
	print "also medium"
else
	print "small"
```

If you don't know what an 'if' is, please learn another programming language first. This is a bad choice for a first language to learn.

'If' works the way you would expect. 'elif' means 'else if'. you can have multiple 'elif's, and you don't need an 'else'. You can include colons, like python. They are optional, though.

```
if a > 3: # Colon present, this is fine
	pass
elif a < 3 # Colon missing, this is aso fine
	fail


if a > 3: pass # SINGLE-LINE IFS WILL NOT PARSE CORRECTLY!
```

Indentation must be done with tabs. Spaces are effectively ignored for the purposes of indentation.


TODO