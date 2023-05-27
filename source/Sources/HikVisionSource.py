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
        # hikutils.deleteXML(self.server, 'System/Video/inputs/channels/' + str(component.address) + '/overlays/text')

    def close_component(self, component_id):
        del self.components[component_id]
        del self.tasks[component_id]
        del self.out_paths[component_id]

    def close_source(self):
        for component in self.components:
            self.close_component(component)

    def write_component(self, component_id, msg):
        if msg:
            if isinstance(self.components[component_id].address, list):
                cams = self.components[component_id].address
            else:
                cams = [self.components[component_id].address]
            for cam in cams:
                cam = str(cam)
                hikutils.putXML(self.server, 'ContentMgmt/record/control/manual/start/tracks/' + cam)
                mask = hikutils.xml2dict(b'\
                                                         <PrivacyMask version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">\
                                                         <enabled></enabled>\
                                                         </PrivacyMask>')
                mask['PrivacyMask']['enabled'] = 'true'
                hikutils.putXML(self.server, 'System/Video/inputs/channels/' + cam[0] + '/privacyMask', mask)
                params = hikutils.xml2dict(b'\
                            <PrivacyMaskRegionList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">\
                            <PrivacyMaskRegion>\
                            <id></id>\
                            <enabled></enabled>\
                            <RegionCoordinatesList>\
                            </RegionCoordinatesList>\
                            <maskType></maskType>\
                            </PrivacyMaskRegion>\
                            </PrivacyMaskRegionList>')
                params['PrivacyMaskRegionList']['PrivacyMaskRegion']['id'] = '1'
                params['PrivacyMaskRegionList']['PrivacyMaskRegion']['enabled'] = 'true'
                params['PrivacyMaskRegionList']['PrivacyMaskRegion']['maskType'] = 'red'
                command = hikutils.dict2xml(params)
                coords = '<RegionCoordinates>\
                                    <positionX>0</positionX>\
                                    <positionY>0</positionY>\
                                </RegionCoordinates>\
                                <RegionCoordinates>\
                                    <positionX>0</positionX>\
                                    <positionY>10</positionY>\
                                </RegionCoordinates>\
                            <RegionCoordinates>\
                                    <positionX>10</positionX>\
                                    <positionY>10</positionY>\
                            </RegionCoordinates>\
                            <RegionCoordinates>\
                                    <positionX>10</positionX>\
                                    <positionY>0</positionY>\
                            </RegionCoordinates>'
                index = command.find('</RegionCoordinatesList>')
                command = command[:index] + coords + command[index:]
                hikutils.putXML(self.server, 'System/Video/inputs/channels/' + cam[0] + '/privacyMask/regions', xmldata=command)
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
            mask = hikutils.xml2dict(b'\
                                     <PrivacyMask version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">\
                                     <enabled></enabled>\
                                     </PrivacyMask>')
            mask['PrivacyMask']['enabled'] = 'false'
            hikutils.putXML(self.server, 'System/Video/inputs/channels/' + addr[0] + '/privacyMask', mask)
            hikutils.putXML(self.server, 'ContentMgmt/record/control/manual/stop/tracks/' + addr)
            hikutils.putXML(self.server, 'ContentMgmt/record/control/manual/stop/tracks/' + addr)
            resp = self.server.ContentMgmt.search.getAllRecordingsForID(addr)
            vids = resp['CMSearchResult']['matchList']['searchMatchItem']
            if not isinstance(vids, list):
                vids = [vids]
            vid = vids[-1]
            dwnld = self.server.ContentMgmt.search.downloadURI(vid['mediaSegmentDescriptor']['playbackURI'])
            output_folder = op.format(subj, datetime.now().strftime("%m-%d-%Y"))
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            with open(output_folder + name + "_" + addr + ".mp4", 'wb') as file:
                file.write(dwnld.content)

    def is_available(self):
        return self.available
