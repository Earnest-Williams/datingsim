from PySide6.QtCore import QObject, Signal

class Bus(QObject):
    # Engine → UI
    scene_changed = Signal(dict)          # {bg, sprites}
    dialogue_ready = Signal(dict)         # {speaker, text, options}
    stats_updated = Signal(dict)          # {name,hp,mp,stamina,level,attrs,skills,conditions,affinity}
    inventory_updated = Signal(list)      # [{id,name,qty},...]
    knowledge_updated = Signal(dict)      # {notes,factions,sites,tech}
    toast = Signal(str)

    # UI → Engine
    option_chosen = Signal(int)
    pane_toggled = Signal(str)            # "left" | "right"
