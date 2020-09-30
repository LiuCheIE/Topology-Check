from shapely.geometry import *
from shapely.geometry import Polygon
import itertools
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from tkinter import scrolledtext as st
import fiona
import pandas as pd

class MyGUI:
    first_shp = ''

    def __init__(self, my_parent):
        self.my_parent = my_parent
        self.my_parent.title("Overlap test")
        my_parent.protocol("WM_DELETE_WINDOW", self.catch_destroy)

        self.first_shp_geojson = StringVar()
        self.merged_filter_key = StringVar()
        self.merged_filter_value = StringVar()
        self.merged_shp_name = StringVar()
        self.centoid_shp_name = StringVar()

        self.frame1 = ttk.Frame(my_parent, padding=5, border=1)
        self.frame1.grid(row=0, column=0)

        self.tasks_frame = LabelFrame(self.frame1, padx=15, pady=15, text="Function")
        self.tasks_frame.grid(row=0, column=0, sticky=NW)

        # Label(self.tasks_frame, text="1.").grid(row=0, column=0, sticky=W)
        Button(self.tasks_frame, text="Select Polygon shapefile", command=self.get_shapefile)\
            .grid(row=0, column=1, sticky=NW, pady=5)
        Button(self.tasks_frame, text="Find overlap", command=self.find_overlap) \
            .grid(row=1, column=1, sticky=NW, pady=5)
        Button(self.tasks_frame, text="Clip overlapping area", command=self.clipping_overlaparea) \
            .grid(row=2, column=1, sticky=NW, pady=5)
        Button(self.tasks_frame, text="Export affected parcels", command=self.save_as_csv) \
            .grid(row=3, column=1, sticky=NW, pady=5)

        self.log_frame = LabelFrame(self.frame1, padx=15, pady=15, text="Log")
        self.log_frame.grid(row=0, column=1, sticky=NW)

        self.log_text = st.ScrolledText(self.log_frame, width=80, height=50, wrap=WORD)
        self.log_text.grid(row=0, column=0)

    def catch_destroy(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.my_parent.destroy()

    def get_shapefile(self):
        global first_shp
        first_shp = filedialog.askopenfilename(filetypes=(("Shapefiles", "*.shp"),))

        self.log_text.insert(END, "-" * 80 + "\n")
        self.log_text.insert(END, "Shapefile selected: {}\n".format(first_shp))

        print(first_shp)

    def find_overlap(self):
        global parcel_dic
        global source_driver
        global source_crs
        global source_schema
        parcel_dic = []
        try:
            out_file = "data/overlap.shp"
            with fiona.open(first_shp, 'r') as sh:
                source_driver = sh.driver
                source_crs = sh.crs
                source_schema = sh.schema
                # print(source_crs)
                for i in sh:
                    if i["geometry"] is not None and i["geometry"]["type"] == "Polygon":
                        parcel_dic.append(i)
                    else:
                        pass
                print(len(parcel_dic))
                num = 0
                global polygon_dic
                polygon_dic = []
                for num in range(len(list(sh))):
                    if sh[num]["geometry"] is not None:
                        meta = sh[num]["geometry"]["coordinates"]
                        # print(meta)
                        polygon_dic.append(meta)
                        # print(polygon_dic)
                        num += 1
                    else:
                        pass
                polygon_point_list = []
                global polygon_list
                print("1")
                polygon_list = []
                for i in range(len(list(polygon_dic))):
                    polygon_point_list = []
                    for n in range(len(list(polygon_dic[i][0]))):
                        polygon_point_list.append(polygon_dic[i][0][n])
                    ext = Polygon(polygon_point_list)
                    polygon_new = Polygon(ext)

                    polygon_list.append(polygon_new)
                print("2")
                global overlap_area
                overlap_area = []
                count_num = 0

                for i in itertools.combinations(polygon_list, 2):
                    try:
                        if i[0].overlaps(i[1]):
                            intersection_area = i[0].intersection(i[1])
                            if mapping(intersection_area)["type"] == "Polygon":
                                # print(mapping(intersection_area)["type"])
                                overlap_area.append(intersection_area)
                                # print(intersection_area)
                                print(count_num)
                                count_num += 1
                            else:
                                pass
                        else:
                            pass
                    except Exception as e:
                        print(e)

                number_of_overlap = len(list(overlap_area))
                print(number_of_overlap, "Overlapping areas")

                # #create new shapefile for overlapping area to check if it works
                with fiona.open(out_file, "w", driver=source_driver,
                                crs=source_crs,
                                schema=source_schema) as new_overlap:
                    a = 0
                    for i in sh:
                        if a < int(number_of_overlap):
                            i["geometry"] = mapping(overlap_area[a])
                            new_overlap.write(i)
                            a += 1
                        else:
                            break
                    self.log_text.insert(END, "-" * 80 + "\n")
                    self.log_text.insert(END, "Overlapping area shapefile has been created!  Location is \"{}\"\n".format(out_file))

        except Exception as e:
            self.log_text.insert(END, "-" * 80 + "\n")
            self.log_text.insert(END, "Something bad happened: {}\n".format(e))
            self.log_text.insert(END, "-" * 80 + "\n")
            return

    def clipping_overlaparea(self):
        global unique_affected_parcel
        affected_parcel = []
        out_file = "data/clipped.shp"
        clipped_parcels = []
        # print(polygon_list)
        delect_overlap_area = []
        num_count = 0

        for i in parcel_dic:
            check_polygon = Polygon(i['geometry']['coordinates'][0]).buffer(0.01)
            overlap_polygon_num = [x for x in range(len(overlap_area)) if check_polygon.contains(overlap_area[x])
                                   if i['properties']["PARCEL_ID"] != "XXXXX" and i['properties']["PARCEL_ID"] != "WHITESP"
                                   if mapping(overlap_area[x])["type"] == "Polygon"]
            try:
                for h in overlap_polygon_num:
                    clipped_parcel = check_polygon.difference(overlap_area[h].buffer(0.1))
                    i['geometry'] = mapping(clipped_parcel)
                    check_polygon = Polygon(i['geometry']['coordinates'][0]).buffer(0.01)
                    affected_parcel.append(i['properties']["PARCEL_ID"])
                    delect_overlap_area.append(overlap_area[h])
                    print(num_count)
                    num_count += 1
            except Exception as e:
                print("Error happens at: ", i['properties']["PARCEL_ID"])
                print(e)
            for kkk in range(len(delect_overlap_area)):
                if delect_overlap_area[kkk] in overlap_area:
                    overlap_area.remove(delect_overlap_area[kkk])
            delect_overlap_area = []


        with fiona.open(out_file, "w", driver=source_driver, crs=source_crs, schema=source_schema) as new_clipped:
            for iii in parcel_dic:
                new_clipped.write(iii)
            print("finish")
            self.log_text.insert(END, "-" * 80 + "\n")
            self.log_text.insert(END, "clipping area shapefile has been created!  Location is \"{}\"\n".format(out_file))
        unique_affected_parcel = list(set(affected_parcel))

    def save_as_csv(self):
        try:
            save_as_file = ""
            save_as_file = filedialog.asksaveasfilename(filetypes=(("Comma-separated values", "*.csv"),))
            name_id = ["Parcel ID"]
            csvfile = pd.DataFrame(columns=name_id, data=unique_affected_parcel)
            csvfile.to_csv(save_as_file, encoding='gbk')

            self.log_text.insert(END, "-" * 80 + "\n")
            self.log_text.insert(END, "Affected parcels have been saved!  Location is \"{}\"\n".format(save_as_file))

        except Exception as e:
            self.log_text.insert(END, "-" * 80 + "\n")
            self.log_text.insert(END, "Someething bad happened: {}\n".format(e))
            self.log_text.insert(END, "-" * 80 + "\n")
            return


def main_gui():
    root = Tk()
    MyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main_gui()