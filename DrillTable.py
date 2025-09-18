import FreeCAD as App

from TechDrawTools.TDToolsUtil import (
    haveView,
    displayMessage,
    QT_TRANSLATE_NOOP,
    getSelView,
    getSelVertexes,
    getSelEdges,
)


class DrillOrigin:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "DrillTable::DrillOrigin"

        # set the zero
        origin = getSelVertexes()
        if len(origin) != 1:
            return False
        origin = origin[0]

        obj.addProperty(
            "App::PropertyString", "Letter", "Base", "Letter to add to holes"
        ).Letter = "A"
        # not great, should probably use a proper length
        obj.addProperty("App::PropertyFloat", "X", "Base", "X point").X = origin.X
        obj.addProperty("App::PropertyFloat", "Y", "Base", "Y point").Y = origin.Y
        obj.addProperty("App::PropertyLink", "TechView", "Base", "View").TechView = (
            getSelView()
        )

        # create measurement spreadsheet
        spread = App.ActiveDocument.addObject("Spreadsheet::Sheet", "DrillTable")
        spread.set("A1", "TAG")
        spread.set("B1", "X LOC")
        spread.set("C1", "Y LOC")
        spread.set("D1", "SIZE")
        obj.addProperty(
            "App::PropertyLink", "Spreadsheet", "Base", "Spreadsheet"
        ).Spreadsheet = spread

        # add the axis on the sheet
        self.clines = []
        self._drawAxisArrow(origin, getSelView())

    def _drawAxisArrow(self, origin, view):
        origin = App.Vector(origin.X, origin.Y)

        def drawArrow(P1, P2, P3, P4, P5):
            self.clines.append(view.makeCosmeticLine(origin, origin + P1, 1))
            self.clines.append(view.makeCosmeticLine(origin + P2, origin + P3, 1))
            self.clines.append(view.makeCosmeticLine(origin + P3, origin + P4, 1))
            self.clines.append(view.makeCosmeticLine(origin + P3, origin + P5, 1))

        P1X, P1Y = App.Vector(0, -10, 0), App.Vector(-10, 0, 0)
        P2X, P2Y = App.Vector(0, -5, 0), App.Vector(-5, 0, 0)
        P3X, P3Y = App.Vector(10, -5, 0), App.Vector(-5, 10, 0)
        P4X, P4Y = App.Vector(7, -4, 0), App.Vector(-4, 7, 0)
        P5X, P5Y = App.Vector(7, -6, 0), App.Vector(-6, 7, 0)
        drawArrow(P1X, P2X, P3X, P4X, P5X)
        drawArrow(P1Y, P2Y, P3Y, P4Y, P5Y)

        xc = origin + P3X + App.Vector(0, -3)
        self.clines.append(
            view.makeCosmeticLine(xc + App.Vector(2, 2), xc + App.Vector(-2, -2))
        )
        self.clines.append(
            view.makeCosmeticLine(xc + App.Vector(-2, 2), xc + App.Vector(2, -2))
        )

        yc = origin + P3Y + App.Vector(-3, 0)
        self.clines.append(
            view.makeCosmeticLine(yc + App.Vector(1, 1), yc + App.Vector(-2, -2), 1)
        )
        self.clines.append(view.makeCosmeticLine(yc + App.Vector(-1, 1), yc))

    def execute(self, obj):
        pass


Gui = App.Gui
translate = App.Qt.translate


class DrillOriginCmd:
    def GetResources(self):
        import os

        __dir__ = os.path.dirname(__file__)
        iconPath = os.path.join(__dir__, "icons")
        return {
            # The name of a svg file available in the resources.
            "Pixmap": os.path.join(iconPath, "origin.svg"),
            "MenuText": translate("DrillTable", "Add Origin"),
            "Accel": "U",
            "ToolTip": translate(
                "DrillTable",
                "Add a new origin and associated drill table.\n"
                "1. Select a vertex on the view.\n"
                "2. Add further circles on the view\n",
            ),
        }

    def IsActive(self):
        if not Gui.Selection.getSelectionEx():
            return False

        return (
            len(
                [
                    s
                    for s in App.Gui.Selection.getSelectionEx()
                    for n in s.SubElementNames
                    if n[0:6] == "Vertex"
                ]
            )
            == 1
        )

    def Activated(self):
        obj = App.ActiveDocument.addObject("App::FeaturePython", "drillorigin")
        DrillOrigin(obj)
        DrillOriginGui(obj.ViewObject)

        App.ActiveDocument.recompute()
        return obj


class DrillOriginGui:
    def __init__(self, obj):
        obj.Proxy = self

    def getIcon(self):
        return """
    /* XPM */
static const char *origin[] = {
/* columns rows colors chars-per-pixel */
"24 24 7 1 ",
"  c black",
". c #310031003100",
"X c #635F635F635F",
"o c #700070007000",
"O c #C986C986C986",
"+ c #E322E322E322",
"@ c None",
/* pixels */
"@@@@@@@@@@@@@@@@@@@@@@@@",
"@@@@@@@@@@@@@@@@@@@@@@@@",
"@@@@O.O@@@@@@@@@@@@@@@@@",
"@@@+   +@@@@@@@@@@@@@@@@",
"@@+     +@@@@@@@@@@@@@@@",
"@+       +@@@@@@@@@@@@@@",
"@o  X X  o@@@@@@@@@@@@@@",
"@+o+o o+o+@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@@@@@@@@",
"@@@@o o@@@@@@@@@@+o+@@@@",
"@@@@o o@@@@@@@@@@o  +@@@",
"@@@@o o@@@@@@@@@@+   +@@",
"@@@@o ooooooooooooX   O@",
"@@@@o                 .@",
"@@@@+oooooooooooooX   O@",
"@@@@@@@@@@@@@@@@@+   +@@",
"@@@@@@@@@@@@@@@@@o  +@@@",
"@@@@@@@@@@@@@@@@@+o+@@@@"
};
"""


class CleanOriginLines:
    """
    Clean up the lines in the technical drawing when the origin is deleted.
    """

    def slotDeletedObject(self, obj):
        if not _isDrawOrigin(obj):
            return

        for cl in obj.Proxy.clines:
            obj.TechView.removeCosmeticEdge(cl)


App.addDocumentObserver(CleanOriginLines())


def _isDrawOrigin(obj) -> bool:
    return (
        obj.TypeId == "App::FeaturePython"
        and hasattr(obj.Proxy, "Type")
        and obj.Proxy.Type == "DrillTable::DrillOrigin"
    )


def _locatePageView():
    # origin is the related DrillOrigin object
    origin = [obj for obj in App.ActiveDocument.Objects if _isDrawOrigin(obj)]
    if not origin:
        print("no origin")
        return False

    origin = origin[0]

    view = App.Gui.Selection.getSelection()
    if not view:
      print("no view")
      return False
    view = view[0]

    # page is the technical drawing of the current view
    page = [
        obj
        for obj in App.ActiveDocument.Objects
        if obj.TypeId == "TechDraw::DrawPage" and view in obj.Views
    ]
    if not page:
        print("no page")
        return False

    page = page[0]

    return (origin, page)


def addinstance():
    view = getSelView()
    origin, page = _locatePageView()

    # last is the last column in the spreadsheet
    last = int(origin.Spreadsheet.getUsedCells()[-1].removeprefix("D"))

    for edge in getSelEdges():
        last = last + 1

        center, radius = edge.Curve.Center, edge.Curve.Radius
        tag = origin.Letter + str(last - 1)

        # insert reference in spreadsheet
        origin.Spreadsheet.set("A" + str(last), tag)
        origin.Spreadsheet.set("B" + str(last), str(center.x - origin.X))
        origin.Spreadsheet.set("C" + str(last), str(center.y - origin.Y))
        origin.Spreadsheet.set("D" + str(last), str(radius * 2))

        # add annotation to the view
        margin_left = 8

        a = App.ActiveDocument.addObject("TechDraw::DrawViewAnnotation", "drilltag")
        page.addView(a)
        a.Text = tag
        a.TextSize = 3
        a.X = float(view.X) + (center.x + radius) * view.Scale + margin_left
        a.Y = float(view.Y) + center.y * view.Scale


class AddHolePosition:
    def GetResources(self):
        import os

        __dir__ = os.path.dirname(__file__)
        iconPath = os.path.join(__dir__, "icons")
        return {
            # The name of a svg file available in the resources.
            "Pixmap": os.path.join(iconPath, "add-hole.svg"),
            "MenuText": translate("DrillTable", "Add Hole"),
            "Accel": "H",
            "ToolTip": translate(
                "DrillTable",
                "Add a new hole to the view drill table\n"
                "1. Select an on the view.\n",
            ),
        }

    def IsActive(self):
        if not _locatePageView():
          return False
        return True

    def Activated(self):
        addinstance()


Gui.addCommand("DrillTable_AddOrigin", DrillOriginCmd())
Gui.addCommand("DrillTable_AddHole", AddHolePosition())
