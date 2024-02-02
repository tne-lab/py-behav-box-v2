import threading
import time
import datetime

from hikload.hikvisionapi.classes import HikvisionServer
import hikload.hikvisionapi.utils as hikutils
import os

from Events import PybEvents
from Sources.Source import Source


class HikVisionSource(Source):

    def __init__(self, ip, user, password):
        super(HikVisionSource, self).__init__()
        self.ip = ip
        self.user = user
        self.password = password
        self.server = None
        self.out_paths = {}
        self.start_times = {}

    def initialize(self):
        self.server = HikvisionServer(self.ip, self.user, self.password)

    def register_component(self, component, metadata):
        self.out_paths[component.id] = None
        # hikutils.deleteXML(self.server, 'System/Video/inputs/channels/' + str(component.address) + '/overlays/text')

    def output_file_changed(self, event: PybEvents.OutputFileChangedEvent) -> None:
        for cid, chamber in self.component_chambers.items():
            if chamber == event.chamber:
                self.out_paths[cid] = event.output_file

    def close_component(self, component_id):
        del self.components[component_id]
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
                self.start_times[cam] = (datetime.datetime.now() - datetime.timedelta(seconds=10)).isoformat().split('.')[0] + 'Z'
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
            threading.Thread(target=self.download, args=[component_id]).start()

    def download(self, component_id):
        output_folder = self.out_paths[component_id]
        name = time.time_ns()
        if isinstance(self.components[component_id].address, list):
            addresses = self.components[component_id].address
        else:
            addresses = [self.components[component_id].address]
        end_time = (datetime.datetime.now() + datetime.timedelta(seconds=10)).isoformat().split('.')[0] + 'Z'
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
            resp = self.server.ContentMgmt.search.getPastRecordingsForID(addr, self.start_times[addr], end_time)
            vids = resp['CMSearchResult']['matchList']['searchMatchItem']
            if not isinstance(vids, list):
                vids = [vids]
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            with open(output_folder + str(name) + "_" + addr + ".mp4", 'wb') as file:
                for i, vid in enumerate(vids):
                    dwnld = self.server.ContentMgmt.search.downloadURI(vid['mediaSegmentDescriptor']['playbackURI'])
                    file.write(dwnld.content)
