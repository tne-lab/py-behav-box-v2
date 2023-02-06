from hikload.hikvisionapi.classes import HikvisionServer
import hikload.hikvisionapi.utils as hikutils
import threading
import os
from datetime import datetime
from Sources.Source import Source


class HikVisionSource(Source):

    def __init__(self, ip, user, password):
        super(HikVisionSource, self).__init__()
        self.ip = ip
        self.user = user
        self.password = password
        try:
            self.server = HikvisionServer(ip, user, password)
            self.available = True
        except:
            self.available = False
        self.out_paths = {}
        self.tasks = {}

    def register_component(self, task, component):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.out_paths[component.id] = "{}\\py-behav\\{}\\Data\\{{}}\\{{}}\\".format(desktop, type(task).__name__)
        self.components[component.id] = component
        self.tasks[component.id] = task

    def close_component(self, component_id):
        del self.components[component_id]
        del self.tasks[component_id]
        del self.out_paths[component_id]

    def close_source(self):
        for component in self.components:
            self.close_component(component)

    def write_component(self, component_id, msg):
        if isinstance(self.components[component_id].address, list):
            cams = self.components[component_id].address
            msgs = [msg] * len(self.components[component_id].address)
        else:
            cams = [self.components[component_id].address]
            msgs = [msg]
        for i, m in enumerate(msgs):
            if m:
                hikutils.putXML(self.server, 'ContentMgmt/record/control/manual/start/tracks/' + str(cams[i]))
                params = {'id': str(cams[i]), 'enabled': True, 'positionX': 0, 'positionY': 0, 'displayText': '■'}
                hikutils.postXML(self.server, 'System/Video/inputs/channels/' + str(cams[i]) + '/overlays/text', params)
        else:
            vt = threading.Thread(target=self.download, args=[component_id])
            vt.start()

    def download(self, component_id):
        op = self.out_paths[component_id]
        name = self.components[component_id].name
        subj = self.tasks[component_id].metadata["subject"]
        if isinstance(self.components[component_id].address, list):
            addresses = self.components[component_id].address
        else:
            addresses = [self.components[component_id].address]
        for addr in addresses:
            addr = str(addr)
            hikutils.deleteXML(self.server, 'System/Video/inputs/channels/' + addr + '/overlays/text')
            hikutils.putXML(self.server, 'ContentMgmt/record/control/manual/stop/tracks/' + addr)
            hikutils.putXML(self.server, 'ContentMgmt/record/control/manual/stop/tracks/' + addr)
            resp = self.server.ContentMgmt.search.getAllRecordingsForID(addr)
            vid = resp['CMSearchResult']['matchList']['searchMatchItem'][-1]
            dwnld = self.server.ContentMgmt.search.downloadURI(vid['mediaSegmentDescriptor']['playbackURI'])
            output_folder = op.format(subj, datetime.now().strftime("%m-%d-%Y"))
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            with open(output_folder + name + "_" + addr + ".mp4", 'wb') as file:
                file.write(dwnld.content)

    def is_available(self):
        return self.available
