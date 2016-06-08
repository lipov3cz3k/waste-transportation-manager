import xml.etree.ElementTree as ET
from ftplib import FTP
from nominatim import NominatimReverse
from os.path import dirname, normpath, basename, join, exists, isfile
from os import listdir, unlink
from sqlalchemy import desc
from time import sleep
from common.config import local_config, ftp_config
from common.utils import LogType, print, parse_filename, TRACE_FN_CALL, DECORATE_ALL, CheckFolders, get_tqdm


@DECORATE_ALL(TRACE_FN_CALL)
class DDRManager:
    ############################### DOWNLOAD DATA ###############################
    def __init__(self):
        print("Initialize DDRManager", LogType.trace)
        self.state = {}
        self.SetState(action="init", percentage=0)
        self.run = False
        self.is_gui = False
        self.db_session = None

    def RemoveDBSession(self):
        if self.db_session:
            self.db_session.remove()

    def SetState(self, action = None, percentage = None):
        if action != None:
            self.state['action'] = action
        if percentage != None:
            self.state['percentage'] = int(percentage)

    def EXCEPTION_DownloadNew(self):
        # remove downloaded
        print("Remove downloaded files", LogType.trace)
        self.RemoveFolderContent(local_config.folder_data_root)

    def EXCEPTION_ParseData(self):
        # remove downloaded
        print("Remove downloaded files", LogType.trace)
        self.RemoveFolderContent(local_config.folder_data_root)

    def EXCEPTION_SaveAllDocToDatabase(self, docs):
        # remove downloaded
        print("Remove downloaded files", LogType.trace)
        self.RemoveFolderContent(local_config.folder_data_root)
        print("Remove parsed doc from database", LogType.trace)
        self.RemoveParsedDocFromDb(docs)

    def EXCEPTION_GetLocationsForCoordsAndMsg(self):
        # remove downloaded
        print("Remove downloaded files", LogType.trace)
        self.RemoveFolderContent(local_config.folder_data_root)

    def Manage(self):
        from ddr.database import init_db, db_session
        init_db()

        self.db_session = db_session

        # download
        print("Start downloading new xml data.", LogType.info)
        try:
            self.DownloadNewData()
        except KeyboardInterrupt:
            self.RemoveDBSession()
            print("KeyboardInterrupt", LogType.error)
            # remove downloaded and stop
            self.EXCEPTION_DownloadNew()
            raise KeyboardInterrupt
        except Exception as e:
            self.RemoveDBSession()
            print("Exception during downloading new xml data: %s" % str(e), LogType.error)
            # remove downloaded and stop
            self.EXCEPTION_DownloadNew()
            return
        print("Downloading new xml data was successful.", LogType.info)

        # parse
        print("Start parsing downloaded data.", LogType.info)
        try:
            docs = self.ParseData(local_config.folder_data_root)
        except KeyboardInterrupt:
            self.RemoveDBSession()
            print("KeyboardInterrupt", LogType.error)
            # remove downloaded and stop
            self.EXCEPTION_ParseData()
            raise KeyboardInterrupt
        except Exception as e:
            self.RemoveDBSession()
            print("Exception during parsing downloaded data: %s" % str(e), LogType.error)
            # remove downloaded and stop
            self.EXCEPTION_ParseData()
            return
        print("Parsing downloaded data was successful.", LogType.info)


        # save to database
        print("Start saving parsed data to database.", LogType.info)
        try:
            self.SaveAllDocToDatabase(docs)
        except KeyboardInterrupt:
            self.RemoveDBSession()
            print("KeyboardInterrupt", LogType.error)
            # remove downloaded and stop
            self.EXCEPTION_SaveAllDocToDatabase(docs)
            raise KeyboardInterrupt
        except Exception as e:
            self.RemoveDBSession()
            print("Exception during saving parsed data to database: %s" % str(e), LogType.error)
            # remove downloaded and stop
            self.EXCEPTION_SaveAllDocToDatabase(docs)
            return
        print("Saving to database was successful.", LogType.info)

        print("Remove downloaded files", LogType.trace)
        self.RemoveFolderContent(local_config.folder_data_root)


        # get location
        print("Start reversing COORD.", LogType.info)
        try:
            coords_without_location = self.GetCoordsWithoutLocation()
            self.GetLocationsForCoordsAndMsg(coords_without_location)
        except KeyboardInterrupt:
            self.RemoveDBSession()
            print("KeyboardInterrupt", LogType.error)
            # remove downloaded and stop
            self.EXCEPTION_GetLocationsForCoordsAndMsg()
            raise KeyboardInterrupt
        except Exception as e:
            self.RemoveDBSession()
            print("Exception during reversing COORD: %s" % str(e), LogType.error)
            # remove downloaded
            self.EXCEPTION_GetLocationsForCoordsAndMsg()
            return
        print("Reversing COORD was successful.", LogType.info)
        self.RemoveDBSession()

    # filter folder - get only last_folder and newer
    def FilterFoldersName(self, folders, last_folder_date):
        print("Get newer folder then '%s'." % last_folder_date, LogType.trace)
        result = []
        for folder in folders:
            folder_date = basename(folder)
            if folder_date >= last_folder_date:
                result.append(folder)

        return result

    # filter xml files - get only newer file than last_file_index
    def FilterFilesName(self, files, last_file_index):
        print("Get newer files then index '%s'." % last_file_index, LogType.trace)
        result = []
        last_file_index = int(last_file_index)
        for file in files:
            file_name = basename(file)
            file_name = file_name.split(".")[0]
            file_name = file_name.split("_")
            file_index = file_name[1]
            if int(file_index) > last_file_index:
                result.append(file)

        return result

    # download file from ftp
    def DownloadFile(self, file_path):
        print("Downloading file: %s" % file_path, LogType.trace)

        path = dirname(file_path)
        filename = basename(normpath(file_path))

        save_file_path = join(local_config.folder_data_root, filename)

        # 2 attempts to download
        for _ in range(2):
            try:
                ftp = FTP(ftp_config.host)
                ftp.login(ftp_config.username, ftp_config.password)

                ftp.cwd(path)
                ftp.retrbinary("RETR " + filename , open(save_file_path, 'wb').write)
                ftp.quit()
            except Exception as e:
                print("Error during downloading file: %s" % str(e), LogType.error)
                if _ == 2:
                     raise e
                print("Try again ...", LogType.trace)
            else:
                break

    # get name of last downloaded file
    def GetLastFilename(self):
        from ddr.ddr_models import DOC
        print("Get last parsed filename" , LogType.trace)

        last_doc = self.db_session.query(DOC).order_by(desc(DOC.obj_id)).first()

        if not last_doc:
            last_filename = local_config.default_last_file_name
        else:
            last_filename = basename(last_doc.file_name)

        print("Last parsed filename: %s" % str(last_filename), LogType.trace)
        return last_filename

    # download new xml files
    def DownloadNewData(self):
        print("Start downloading ...", LogType.info)
        last_filename = self.GetLastFilename()

        parsed_last_filename = parse_filename(last_filename)

        print("Get folders, filter already used", LogType.trace)
        for _ in range(2):
            try:
                ftp = FTP(ftp_config.host)
                ftp.login(ftp_config.username, ftp_config.password)

                data_folders = ftp.nlst(ftp_config.data_folder_root)
                data_folders = self.FilterFoldersName(data_folders, parsed_last_filename['date'])
            except Exception as e:
                if str(e) == "550 No files found":
                    print("There are no folders.", LogType.warning)
                    break

                print("Error during getting folders: %s" % str(e), LogType.error)
                if _ == 2:
                     raise e
                print("Try again ...", LogType.trace)
            else:
                break

        downloaded_data_count = 0
        for folder in data_folders:
            self.TestIsRun()

            print("Get xml files name, filter already used", LogType.trace)
            for _ in range(2):
                try:
                    xml_files = ftp.nlst(folder)
                    if basename(folder) == parsed_last_filename['date']:
                        xml_files = self.FilterFilesName(xml_files, parsed_last_filename['index'])
                except Exception as e:
                    if str(e) == "550 No files found":
                        print("There are no files.", LogType.warning)
                        break

                    print("Error during getting xml files: %s" % str(e), LogType.error)
                    if _ == 2:
                         raise e
                    print("Try again ...", LogType.trace)

                    ftp = FTP(ftp_config.host)
                    ftp.login(ftp_config.username, ftp_config.password)
                else:
                    break

            for xml_file in get_tqdm(xml_files, self.SetState, desc="downloading XMLs", total=local_config.data_count_per_iteration if local_config.data_count_per_iteration < len(xml_files) else None):
                self.TestIsRun()

                if downloaded_data_count == local_config.data_count_per_iteration:
                    print("Download xml files reach limit", LogType.trace)
                    return

                try:
                    self.DownloadFile(xml_file)
                    downloaded_data_count += 1
                except Exception as e:
                    raise e

    ############################### PARSE DATA ###############################

    # http://www.ariel.com.au/a/python-point-int-poly.html
    # GPS polygon should be used from http://www.birdtheme.org/useful/v3tool.html
    def IsPointInsidePolygon(self, x,y,poly):
        n = len(poly)
        inside =False

        p1x,p1y = poly[0]
        for i in range(n+1):
            p2x,p2y = poly[i % n]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x,p1y = p2x,p2y

        return inside

    # get parsed xml from xml file as root
    def GetRootFromXmlFile(self, xml_path):
        print("Parse xml file to root \"%s\"." % xml_path, LogType.trace)
        if not exists(xml_path):
            raise FileNotFoundError("Cannot find \"%s\"." % (xml_path))

        try:
            contains_cdata = False
            with open(xml_path, 'r', encoding="utf8") as xml_file:
                try:
                    contents = xml_file.read()
                except :
                    print("Cannot read file: " + xml_file, LogType.error)
                    raise IOError("Cannot read file: " + xml_file)
                else:
                    contains_cdata = contents.count("[CDATA[") > 0
                    xml_file.close()

            with open(xml_path, 'r', encoding="utf8") as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                if contains_cdata:
                    root = root.find(".//{http://www.praha.eu/iskr/WSDL/GISluzbyGIS}xml")
                    root = ET.fromstring(root.text)

                xml_file.close()
                return root
        except Exception as e :
            raise Exception("Cannot open or parse xml file \"%s\". Error: %s" % (xml_path, str(e)))

    # get xml files name from folder
    def GetXmlFilesPath(self, folder_path):
        print("Getting xml files path list", LogType.trace)
        folder_path = normpath(folder_path)
        xml_files = []
        for filename in listdir(folder_path):
            if not filename.endswith('.xml'): continue
            xml_files.append(join(folder_path, filename))

        return xml_files

    # return tuple (file_path, root-parsed_xml)
    def GetParsedXmlFiles(self, xml_files):
        print("Parse xml files", LogType.trace)
        roots = []
        for file_path in xml_files:
            self.TestIsRun()
            try :
                roots.append((file_path, self.GetRootFromXmlFile(file_path)))
            except Exception as e :
                print("Cannot parse xml: %s" % (str(e)), LogType.error)

        return roots

    # parse xml root into database models
    def GetDocFromParsedXml(self, parsed_xml):
        from ddr.ddr_models import DOC
        print("Parse root to objects", LogType.trace)

        xml_path = parsed_xml[0]
        root = parsed_xml[1]
        doc = DOC(root, xml_path)
        return doc

    # save doc object to database
    def SaveDocToDatabase(self, doc_obj):
        print("Save DOC object to database (%s)" % basename(doc_obj.file_name), LogType.trace)

        self.db_session.add(doc_obj)
        self.db_session.commit()

    def SaveAllDocToDatabase(self, docs):
        print("Saving DOC objects to database", LogType.trace)
        for doc in get_tqdm(docs, self.SetState, desc="saving docs to db", total=None):
            self.TestIsRun()

            self.SaveDocToDatabase(doc)

    # parse all xml root into database models
    def GetDocsFromParsedXmls(self, parsed_xmls):
        print("Getting docs from parsed xml files", LogType.trace)
        docs = []
        for parsed_xml in get_tqdm(parsed_xmls, self.SetState, desc="getting docs from parsed xml", total=None):
            self.TestIsRun()

            doc = self.GetDocFromParsedXml(parsed_xml)
            docs.append(doc)

        return docs

    def LoadAllDocsFromDb(self):
        from ddr.ddr_models import DOC

        docs_tuple = self.db_session.query(DOC).all()

        return docs_tuple

    def GetLocationsForCoordsAndMsg(self, coords_array):
        from ddr.ddr_models import Location
        print("Getting locations for COORDS <%d> (use Nominatim)" % len(coords_array), LogType.trace)
        nominatim = NominatimReverse()
        for coord_obj in get_tqdm(coords_array, self.SetState, desc="getting locations", total=None):
            self.TestIsRun()

            successful = False
            coords = coord_obj.get_coordinations(self.db_session)
            if str(coords["x"]) == "NaN" or str(coords["y"]) == "NaN":
                print("Coord has NaN, skipping ...", LogType.warning)
                continue

            if coords["coordsystem"] == "WGS-84":
                location_data = self.GetStoredLocation(coords["x"], coords["y"])
                print("Get location for \"%s\": " % (str(basename(coord_obj.get_doc_filename(self.db_session)))), LogType.trace, has_EOL=False)
                if location_data == None:
                    print("getting new by nominatim ...", LogType.trace, only_Message=True)
                    while not successful:
                        try:
                            location = nominatim.query(lat=coords["x"], lon=coords["y"], zoom=16)
                        except Exception as e:
                            raise e
                        else:
                            successful = True
                    address = location['address']
                    osm_id = location['osm_id']
                    location_obj = Location(address, osm_id)
                else:
                    print("reusing already stored ...", LogType.trace, only_Message=True)
                    location_obj = Location(location_data, location_data['osm_id'])
                # set location for COORD and MSG
                coord_obj.set_Location(location_obj)
                self.GetMsgForCoord(coord_obj).set_Location(location_obj)
                self.db_session.add(coord_obj)
                self.db_session.commit()
            else :
                print("Bad coordsystem: ", coords["coordsystem"], LogType.warning)

        print("Getting locations finished", LogType.trace)

    def GetStoredLocation(self, x, y):
        from ddr.ddr_models import COORD

        print("Try to get already reversed coordination from local database.", LogType.trace)

        coord_obj = self.db_session.query(COORD).filter(COORD.x == x, COORD.y == y).first()
        if coord_obj:
            location_obj = coord_obj.Location
            if location_obj:
                location_data = {
                    'osm_id' : location_obj.osm_id,
                    'city' : location_obj.city,
                    'village' : location_obj.village,
                    'town' : location_obj.town,
                    'hamlet' : location_obj.hamlet,
                    'house_number' : location_obj.house_number,
                    'country' : location_obj.country,
                    'postcode' : location_obj.postcode,
                    'road' : location_obj.road
                }
                return location_data


        return None


    def IsDocInDb(self, doc):
        from ddr.ddr_models import DOC

        doc_obj = self.db_session.query(DOC).filter(DOC.id == doc.id).first()
        if not doc_obj:
            return False
        else:
            return True

    def HasAllCoordInDocLocation(self, doc):
        from ddr.ddr_models import DOC

        doc_obj = self.db_session.query(DOC).filter(DOC.id == doc.id).first()
        if doc_obj.MJD:
            for ddr_message in doc.MJD.MSG :
                coord_obj = ddr_message.get_coord_object()
                if not coord_obj.Location:
                    return False

        return True

    def RemoveFolderContent(self, folder):
        for the_file in listdir(folder):
            file_path = join(folder, the_file)
            try:
                if isfile(file_path):
                    unlink(file_path)
            except Exception as e:
                print(e, LogType.error)

    def RemoveParsedDocFromDb(self, docs):
        for doc in docs:
            if self.IsDocInDb(doc):
                self.db_session.delete(doc)
                self.db_session.commit()

    def RemoveParsedDocWithoutLocationFromDb(self, docs):
        for doc in docs:
            if self.IsDocInDb(doc) and not self.HasAllCoordInDocLocation(doc):
                self.db_session.delete(doc)
                self.db_session.commit()

    #return parsed docs in database models
    def ParseData(self, folder):
        # list dir and get path for only .xml files
        xml_files = self.GetXmlFilesPath(folder)

        # parse XML files
        parsed_xmls = self.GetParsedXmlFiles(xml_files)

        # TODO: filter only coords in specifics polygon
        # get DOC from all parsed XML files and save it to database
        docs = self.GetDocsFromParsedXmls(parsed_xmls)

        return docs

    def GetCoordsWithoutLocation(self):
        from ddr.ddr_models import COORD

        coords_obj = self.db_session.query(COORD).filter(COORD.Location == None).all()
        return coords_obj

    def GetMsgForCoord(self, coord):
        if coord.SNTL:
            return coord.SNTL[0].MLOC[0].MSG[0]
        elif coord.WDEST:
            return coord.WDEST[0].MSG[0]

    def TestIsRun(self):
        if not self.run:
            raise Exception("Service not running")

def Run():
    CheckFolders()
    print("Running from terminal ...", LogType.info)
    ddr_manager = DDRManager()
    ddr_manager.run = True
    while True:
        try:
            print("Manage started", LogType.info)
            ddr_manager.Manage()
        except KeyboardInterrupt:
            ddr_manager.run = False
            print("KeyboardInterrupt", LogType.info)
            break
        except Exception as e:
            print("Console exception: %s " % str(e), LogType.error)

        try:
            print("Manage ended", LogType.info)
            print("Waiting to next iteration ...", LogType.info)
            sleep(local_config.sleep_between_iteration/1000)
        except KeyboardInterrupt:
            ddr_manager.run = False
            print("KeyboardInterrupt", LogType.info)
            break

    print("Terminal running stopped", LogType.info)

if __name__ == '__main__':
    Run()