class Question:
    def __init__(self, unit, part, text, co, bloom):
        self.unit = int(unit)   # 🔥 CRITICAL FIX
        self.part = part
        self.text = text
        self.co = co
        self.bloom = bloom   # K1, K2...

    def to_dict(self):
        return {
            "unit": self.unit,
            "part": self.part,
            "text": self.text,
            "co": self.co,
            "bloom": self.bloom
        }
    
    def __eq__(self, other):
        if not isinstance(other, Question):
            return False
        return (self.unit == other.unit and
                self.part == other.part and
                self.text == other.text)