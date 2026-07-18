from enum import Enum

class Category(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    SHOES = "shoes"
    BAG = "bag"
    ACCESSORY = "accessory"
    JEWELLERY = "jewellery"
    HEADWEAR = "headwear"
    SCARF = "scarf"
    BELT = "belt"
    OUTERWEAR = "outerwear"
    DRESS = "dress"

class Pattern(str, Enum):
    SOLID = "solid"
    STRIPED = "striped"
    FLORAL = "floral"
    GRAPHIC = "graphic"
    CHECKERED = "checkered"
    ANIMAL = "animal"
    ABSTRACT = "abstract"

class Style(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    STREETWEAR = "streetwear"
    BUSINESS = "business"
    ATHLETIC = "athletic"
    VINTAGE = "vintage"

class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL = "all"

class Occasion(str, Enum):
    EVERYDAY = "everyday"
    WORK = "work"
    PARTY = "party"
    SPORT = "sport"
    FORMAL = "formal"
    OUTDOOR = "outdoor"

class BodyShape(str, Enum):
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    INVERTED_TRIANGLE = "inverted_triangle"
    HOURGLASS = "hourglass"
    OVAL = "oval"
    ATHLETIC = "athletic"

class SkinTone(str, Enum):
    FAIR = "fair"
    LIGHT = "light"
    MEDIUM = "medium"
    OLIVE = "olive"
    BROWN = "brown"
    DARK = "dark"

class HeightCategory(str, Enum):
    SHORT = "short"
    AVERAGE = "average"
    TALL = "tall"

class Build(str, Enum):
    SLIM = "slim"
    ATHLETIC = "athletic"
    AVERAGE = "average"
    FULL = "full"

class ShoulderWidth(str, Enum):
    NARROW = "narrow"
    AVERAGE = "average"
    BROAD = "broad"

class WaistDefinition(str, Enum):
    DEFINED = "defined"
    AVERAGE = "average"
    UNDEFINED = "undefined"
    
class BodyOrientation(str, Enum):
    FRONT = "front"
    FRONT_LEFT = "front_left"
    FRONT_RIGHT = "front_right"
    SIDE_LEFT = "side_left"
    SIDE_RIGHT = "side_right"
    BACK = "back"

class Pose(str, Enum):
    STANDING = "standing"
    WALKING = "walking"
    SITTING = "sitting"
    OTHER = "other"