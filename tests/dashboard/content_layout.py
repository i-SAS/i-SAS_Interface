from isas.dashboard.qt.base_content_layout import BaseContentLayout
from isas.dashboard.qt.layout import Layout


class ContentLayout(BaseContentLayout):
    def __call__(self):
        return {'tab_name': self.tab}

    def tab(self, parent=None):
        layout = Layout('vbox', parent)
        layout.addSubpackage('visualization_template_dropdowns')
        layout.addSubpackage('visualization_template_textdrawer')
        return layout
