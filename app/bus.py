from PySide6.QtCore import QObject, Signal

class Bus(QObject):
    # Engine → UI
    scene_changed = Signal(dict)          # {bg, sprite}
    dialogue_ready = Signal(dict)         # {speaker, text, options}
    nav_ready = Signal(dict)              # {location, exits:[{id,label}], characters:[str]}
    state_changed = Signal(str)           # "day" | "dialogue" | "date"
    stats_updated = Signal(dict)          # {name,hp,mp,stamina,level,attrs,skills,conditions,affinity}
    inventory_updated = Signal(list)      # [{id,name,qty},...]
    knowledge_updated = Signal(dict)      # {notes,factions,sites,tech}
    toast = Signal(str)

    # UI → Engine
    option_chosen = Signal(int)
    travel_chosen = Signal(str)           # exit key (e.g., "north", "club")
    talk_to = Signal(str)                 # girl name
    pane_toggled = Signal(str)            # "left" | "right"
