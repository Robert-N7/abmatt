from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QHBoxLayout, QSpinBox


class KCLCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.__init_ui()
        self.code = 0
        self.show()

    def calc_flag(self):
        kcl_type = self.type_selection.currentIndex()
        if kcl_type < 0:
            kcl_type = 0
        w = self.trickable.isChecked() | self.drivable.isChecked() << 1 | self.no_bounce.isChecked() << 2
        x = self.intensity.value()
        y = self.shadow.value()
        z = self.basic_effect.currentIndex()
        if z < 0:
            z = 0
        variant = w << 8 | x << 6 | y << 3 | z
        flag = kcl_type | variant << 5
        if int(self.flag.text(), 16) != flag:
            self.flag.setText('{:04X}'.format(flag))

    def on_flag_change(self):
        try:
            flag = int(self.flag.text(), 16)
            if not 0 <= flag <= 0xffff:
                raise ValueError(self.flag.text())
            kcl_type = flag & 0x1f
            if self.type_selection.currentIndex() != kcl_type:
                self.type_selection.setCurrentIndex(kcl_type)
            variant = flag >> 5
            w = variant >> 8 & 0x7
            x = variant >> 6 & 0x3
            y = variant >> 3 & 0x7
            z = variant & 0x7
            if self.basic_effect.currentIndex() != z:
                self.basic_effect.setCurrentIndex(z)
            if self.shadow.value() != y:
                self.shadow.setValue(y)
            if self.intensity.value() != x:
                self.intensity.setValue(x)
            if self.trickable.isChecked() != w & 0x1:
                self.trickable.setChecked(w & 0x1)
            if self.drivable.isChecked() != w & 0x2:
                self.drivable.setChecked(w & 0x2)
            if self.no_bounce.isChecked() != w & 0x4:
                self.no_bounce.setChecked(w & 0x4)
        except ValueError:
            self.flag.setText('{:04X}'.format(0))

    def on_basic_effect_change(self):
        self.calc_flag()

    def on_type_change(self):
        self.basic_effect.clear()
        current = self.type_selection.currentText()
        self.basic_effect.addItems(self.items[current])
        self.calc_flag()

    def on_trick_change(self):
        self.calc_flag()

    def on_no_drive_change(self):
        self.calc_flag()

    def on_no_bounce_change(self):
        self.calc_flag()

    def on_intensity_change(self):
        self.calc_flag()

    def on_shadow_change(self):
        self.calc_flag()

    def __init_ui(self):
        main_layout = QHBoxLayout()
        self.left_widget = QWidget(self)
        main_layout.addWidget(self.left_widget)
        # LEFT
        layout = QGridLayout()
        self.type_label = QLabel('Type')
        layout.addWidget(self.type_label)
        self.type_selection = QComboBox(self)
        unknown = 'Unknown'
        uk_array = [unknown] * 8
        self.items = {
            'Road':['Normal', 'Dirt, GFX on slots 7.3 and 8.3', 'Gravel/Stone', 'Smooth', 'Wood', 'Snow with GFX',
                         'Metal Grate', 'Normal, but sound cuts off'],
             'Slippery Road 1':['White Sand', 'Dirt', 'Water', 'Snow', 'Grass', 'Yellow Sand',
                                    'Sand, no GFX', 'Dirt, no GFX'],
             'Weak Off-Road':['Orange Sand', 'Dirt', 'Water', 'Grass, darker GFX', 'Sand, lighter GFX', 'Carpet',
                                  'Gravel', 'Gravel, different impact SFX'],
            'Off-Road':['Sand', 'Dirt', 'Mud', 'Water, no GFX', 'Grass', 'Sand, lighter GFX',
                            'Gravel, different impact SFX', 'Carpet'],
             'Heavy Off-Road':['Sand', 'Dirt', 'Mud', 'Flowers', 'Grass', 'Snow', 'Sand', 'Dirt, no GFX'],
             'Slipppery Road 2':['Ice', 'Mud', 'Water', 'Normal road, different sound'],
             'Boost Pad':['Default', 'If used and casino_roulette is nearby, the road rotates everything around counter-clockwise',
                              unknown, unknown, unknown, unknown, unknown, unknown],
             'Boost Ramp':['2 Flips', '1 Flip', 'No flips'],
             'Jump Pad':['Stage 2, GBA BC3', 'Stage 3, SNES GV2', 'Stage 1, GBA SGB', 'Stage 4, MG',
                             'Stage 5, Bouncy Mushroom', 'Stage 4, Chain Chomp Wall', 'Stage 2, DS YF and Funky Stadium',
                             'Stage 4, unused'],
             'Item Road':[unknown, unknown, 'Used on metaal grates', 'Used on wooden paths/grass/mushrooms',
                              unknown, 'Used on grass/bushes', unknown],
             'Solid Fall':['Sand', 'Underwater', 'Unknown', 'Ice', 'Dirt', 'Grass', 'Wood', 'Unknown'],
             'Moving Road':['Water following route', 'Water following route, pulls player downwards',
                                'Water following route, pulls player', 'Moving water no route, pulls player down',
                                'Moving asphalt', 'Moving asphalt', 'Moving road', 'Unknown'],
             'Wall':['Normal', 'Rock', 'Metal', 'Wood', 'Ice', 'Bush', 'Rope', 'Rubber'],
             'Invisible Wall':['No spark and SFX', 'Spark and SFX', 'Spark and SFX', 'Unknown', 'Unknown',
                                   'Unknown', 'Unknown', 'Unknown'],
            'Item Wall':['Unknown', 'Unknown, used on rock walls', 'Unknown, used on metal walls', 'Unknown', 'Unknown',
                             'Unknown, used on grass/bushes', 'Unknown'],
            'Wall 3':['Normal', 'Rock', 'Metal', 'Wood', 'Ice', 'Bush', 'Rope', 'Rubber'],
            'Fall Boundary':['Air Fall', 'Water, setting 1 refers to index in KMP', 'Lava, setting 1 refers to index in KMP',
                                 'Icy Water, setting 1 refers to index in KMP (6.1)', 'Lava, no GFX', 'Burning Air Fall',
                                 'Quicksand', 'Short Fall'],
             'Cannon Activator':['Point 0', 'Point 1', 'Point 2', 'Point 3', 'Point 4', 'Point 5', 'Point 6', 'Point 7'],
             'Force Recalculation':['Recalculation 0', 'Recalculation 1', 'Recalculation 2', 'Recalculation 3',
                                        'Recalculation 4', 'Recalculation 5', 'Recalculation 6', 'Recalculation 7'],
             'Half-Pipe Ramp':['Default', 'Boost pad applied, used in Bowsers Castle', 'Unknown', 'Unknown', 'Unknown',
                                   'Unknown', 'Unknown', 'Unknown'],
             'Wall 2':['Normal', 'Rock', 'Metal', 'Wood', 'Ice', 'Bush', 'Rope', 'Rubber'],
             'Moving Road 2':['Moves west with BeltCrossing and escalator', 'Moves east with BeltCrossing and west with escalator.',
                                'Moves east with BeltEasy', 'Moves west with BeltEasy', 'Rotates around BeltCurveA clockwise',
                                'Rotates around BeltCurveA counterclockwise'],
             'Gravity Road':['Wood', 'Gravel, different impact SFX', 'Carpet', 'Dirt, no GFX', 'Sand, different impact and drift SFX, no GFX',
                                 'Normal Road, SFX on 4.4', 'Normal road', 'Mud with GFX'],
             'Road 2':['Normal road, different sound', 'Carpet', 'Grass, GFX on 8.3', 'Normal road, used on green mushrooms',
                         'Grass', 'Glass road with SFX', 'Dirt', 'Normal Road, SFX on 4.4'],
             'Sound Trigger':['Sound Trigger 0', 'Sound Trigger 1', 'Sound Trigger 2', 'Sound Trigger 3', 'Sound Trigger 4',
                                  'Sound Trigger 5', 'Sound Trigger 6', 'Sound Trigger 7'],
             'Unknown':uk_array,
             'Effect Trigger':['BRSTM reset', 'Enable Shadow Effect', 'Water Splash', 'Stargate Activation',
                                   'Unknown', 'Unknown', 'Unknown', 'Unknown'],
             'Unknown 2':uk_array,
             'Half-pipe Invisible Wall':uk_array,
             'Moving Road 3':['Carpet, different impact SFX', 'Normal Road, different sound', 'Normal Road', 'Glass Road',
                                'Carpet', 'No sound, star crash impact SFX (requires starGate)', 'Sand', 'Dirt'],
             'Special Walls':['Cacti effect', 'Fast:bump (rubber wall)', 'Fast:spark, hollow, bump, slow:many bumps',
                                  'Fast:bump',
                                  'Fast:spark, bump, SFX on 4.4', 'Fast:spark, cracking, bump', 'Fast:spark, metal, bump',
                                  'Fast:spark, Star Ring crash, bump, Slow:Star Ring crash'],
             'Player Wall':['Fast Bump'] * 8}
        self.type_selection.addItems(self.items.keys())
        self.type_selection.currentIndexChanged.connect(self.on_type_change)
        layout.addWidget(self.type_selection, 0, 1)
        self.basic_effect_label = QLabel('Basic Effect')
        layout.addWidget(self.basic_effect_label)
        self.basic_effect = QComboBox(self)
        self.basic_effect.addItems(self.items['Road'])
        self.basic_effect.currentIndexChanged.connect(self.on_basic_effect_change)
        layout.addWidget(self.basic_effect, 1, 1)
        self.flag_label = QLabel('KCL Flag')
        layout.addWidget(self.flag_label)
        self.flag = QLineEdit('{:04X}'.format(0), self)
        self.flag.textChanged.connect(self.on_flag_change)
        layout.addWidget(self.flag, 2, 1)
        self.left_widget.setLayout(layout)

        # RIGHT
        layout = QGridLayout()
        self.right_widget = QWidget(self)
        main_layout.addWidget(self.right_widget)
        self.trickable = QCheckBox('Trickable')
        self.trickable.stateChanged.connect(self.on_trick_change)
        layout.addWidget(self.trickable)
        self.drivable = QCheckBox('Not drivable')
        self.drivable.stateChanged.connect(self.on_no_drive_change)
        layout.addWidget(self.drivable)
        self.no_bounce = QCheckBox('No Bounce')
        self.no_bounce.stateChanged.connect(self.on_no_bounce_change)
        layout.addWidget(self.no_bounce)
        self.intensity_label = QLabel('Intensity')
        layout.addWidget(self.intensity_label)
        self.intensity = QSpinBox(self)
        self.intensity.setRange(0, 3)
        self.intensity.valueChanged.connect(self.on_intensity_change)
        layout.addWidget(self.intensity, 3, 1)
        self.shadow_label = QLabel('Shadow', self)
        layout.addWidget(self.shadow_label)
        self.shadow = QSpinBox(self)
        self.shadow.setRange(0, 7)
        self.shadow.valueChanged.connect(self.on_shadow_change)
        layout.addWidget(self.shadow, 4, 1)
        self.right_widget.setLayout(layout)
        self.setLayout(main_layout)
