# robot-2023
## Notes
### Python version
ev3dev uses an older Python version, so features in newer versions are not available (notably f-strings, use `str.format()` instead)

### Orientation of joystick axes
PS4 controller:
```
        y 0
         |
x 0  --- o --- x 255
         |
       y 255
```

MoveJoystick:
```
          y +100
            |
x -100  --- o --- x 100
            |
          y -100
```

As shown above, the sign (+/-) of the y-axis of `MoveJoystick` is the opposite of the PS4 joystick's while for the x-axis it is the same for both.

A full-forward joystick in the y-axis is `0` (lowest value) for the PS4 while it's `+100` (highest value) for `MoveJoystick`.