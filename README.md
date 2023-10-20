### Output Event Structure
```
interface Action {
    type: [audio/video/image], string
    url: string,
    duration: [optional] float
}

interface VisualAction extends Action {
    type: image, video
    position_x: int
    position_y: int
    width: int
    height: int
}

interface AudioAction extends Action {
    type: audio, string
}

interface OutputEvent {
    steps: list[Action]
}
```
