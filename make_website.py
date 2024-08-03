import requests
from urllib.parse import quote
from PIL import Image
import json
import sys, os, glob, shutil
import re
import subprocess
from pathlib import Path
from tqdm import tqdm

#config
root_movies = "./nube"
out_dir = "./out"
tmp_dir = "./tmp"
lang = "es-ES" #"en-US"

lang_path = f"{out_dir}/{lang}"
thumbs_path = Path(f"{lang_path}/thumbs")

os.makedirs(lang_path, exist_ok=True)
os.makedirs(thumbs_path, exist_ok=True)
################

posters_path = f"{tmp_dir}/{lang}/posters"
movie_files_path = f"{tmp_dir}/movie_files.json"
movies_imdb_path = f"{tmp_dir}/{lang}/movies_imdb.json"
movie_ffprobes_path = f"{tmp_dir}/movie_ffprobes.json"

os.makedirs(posters_path, exist_ok=True)
##################


#################
def is_movie(title):
    if title[-3:] not in ["avi", "mkv", "mp4"]:
        return False
    return True

def gen_movie_files(root_movies):
    base = {}

    files = glob.glob(root_movies + "/**", recursive=True)
    for file in files:
        f = Path(file)
        path = str(f.parent.resolve())
        name = str(f.name)

        if (is_movie(name)):
            if path not in base:
                base[path] = []
            base[path].append(name)

    save_movies_files(base)


def load_movies_files():
    try:
        with open(movie_files_path,"r") as f:
            base = json.load(f)
            return base
    except:
        print("cant load movie_files.json")
        sys.exit()

def save_movies_files(base):
    with open(movie_files_path,"w") as f:
        f.write(json.dumps(base))

#####################
def search(lang, title, year):
    title = quote(title)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    url = f"https://api.themoviedb.org/3/search/movie?api_key=f090bb54758cabf231fb605d3e3e0468&language={lang}&query={title}&year={year}"
    r = requests.get(url, headers=headers)
    if (r.status_code==200):
        j= r.json()
        return j
    return None

def myprint(lang, x, ep):
    x = list(x[0])
    if len(ep)==0:
        ep=""
    else:
        ep=ep[0]

    return search(lang, x[0], x[1])["results"]

def get_imdb(lang, title):            
    ep = re.findall(r"S\d\d?E\d\d|ep\d\d|\dx\d\d", title)

    x = re.findall(r"(.+)-?\.?\((\d\d\d\d)\).*", title)
    if len(x)>0 and len(x[0])>=2:
        return myprint(lang, x, ep)

    x = re.findall(r"(.+)-?\.?\[(\d\d\d\d)\].*", title)
    if len(x)>0 and len(x[0])>=2:
        return myprint(lang, x, ep)

    x = re.findall(r"(.+)-?\.?(\d\d\d\d).*", title)
    if len(x)>0 and len(x[0])>=2:
        return myprint(lang, x, ep)
    return None

def load_movies_imdb():
    try:
        with open(movies_imdb_path,"r") as f:
            movies_imdb = json.load(f)
            return movies_imdb
    except:
        movies_imdb = {}
        return movies_imdb

def save_movies_imdb(movies_imdb):
    with open(movies_imdb_path,"w") as f:
        f.write(json.dumps(movies_imdb))

def fetch_movies_imdb():
    base = load_movies_files()
    files = list(base.values())
    files = [ file for f in files for file in f]
    
    movies_imdb = load_movies_imdb()

    print("movie count: %i" % len(movies_imdb.keys()))

    # delete deleted movies                
    keys_to_delete = []
    for title in movies_imdb.keys():
        if title not in files:
            keys_to_delete.append(title)

    for title in keys_to_delete:
        del movies_imdb[title]        

    print("before count: %i" % len(movies_imdb.keys()))

    bad_movies = []
    for title in tqdm(files):
        if title in movies_imdb:
            continue
        data = get_imdb(lang, title)        
        if data!=None and len(data)>0:
            movies_imdb[title] = data[0]
        else:
            bad_movies.append(title)

    print("after count: %i" % len(movies_imdb.keys()))

    with open(f"{out_dir}/bad_movies.json","w") as f:
        f.write(json.dumps(bad_movies))

    save_movies_imdb(movies_imdb)

###########################
def load_movie_ffprobes():
    try:
        with open(movie_ffprobes_path,"r") as f:
            base = json.load(f)
            return base
    except:
        return {}
        

def save_movie_ffprobes(movie_props):
    with open(movie_ffprobes_path,"w") as f:
        f.write(json.dumps(movie_props))


def generate_movie_ffprobes():
    movie_files = load_movies_files()

    folders = movie_files.keys()
    
    filenames = []
    for folder in folders:
        for movie in movie_files[folder]:            
            filenames.append((folder, movie))

    movie_props = load_movie_ffprobes()

    new_files = 0
    for folder, movie in tqdm(filenames):
        if (movie in movie_props):
            continue

        filename = folder + "/" +  movie
        cmd = ["ffprobe", "-v","quiet", "-print_format", "json", "-show_format", "-show_streams",  filename ]       
        #cmd = ["ls", "-al", filename]
        process = subprocess.run(cmd, capture_output=True)
        data = json.loads(process.stdout)
        movie_props[movie] = data
        new_files += 1

    if (new_files>0):
        save_movie_ffprobes(movie_props)


def get_posters(posters_path):
    base = load_movies_imdb()

    os.makedirs(posters_path, exist_ok=True)
    for k,v in tqdm(base.items()):        
        pp = v["poster_path"]
        if (pp!=None):    
            path = f"{posters_path}{pp}"
            if os.path.isfile(path)==False:
                r = requests.get(f"https://image.tmdb.org/t/p/original{pp}")
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024): 
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)

def make_thumbs(posters_path, thumbs_path):
    base_width = 200
    for file in tqdm(glob.glob(f"{posters_path}/*.jpg")):
        out_file = thumbs_path / Path(file).name 
        if os.path.isfile(out_file)==False:
            img = Image.open(file)
            wpercent = (base_width / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((base_width, hsize), Image.LANCZOS)
            img.save(out_file)    

def get_lang(t):
    t = t.lower()
    if t.startswith("cas") or t.startswith("esp") or t.startswith("spa"):
        return "esp"
    if t.startswith("ing") or t.startswith("eng"):
        return "eng"
    if t.startswith("ita"):
        return "ita"
    if t.startswith("fre") or t.startswith("fra"):
        return "fra"
    return None

def generate_processed_movie_database():
    movie_idbm = load_movies_imdb()
    movie_props = load_movie_ffprobes()

    simple_movie_props = {}

    for movie in tqdm(movie_props.keys()):
        
        if movie not in movie_idbm:
            continue

        movie_desc = movie_idbm[movie]

        sm = {}

        sm["title"] = movie_desc["title"]
        sm["date"] = movie_desc["release_date"]
        sm["genre_ids"] = movie_desc["genre_ids"]
        sm["thumb"] = movie_desc["poster_path"]
        sm["overview"] = movie_desc["overview"]

        props = movie_props[movie]
        format = props["format"]
        streams = props["streams"] 

        sm["aud_langs"]=[]
        sm["sub_langs"]=[]
        for p in streams:
            languages = None
            if "tags" in p:
                tags = p["tags"]
                if languages==None:    
                    if "language" in tags:
                        languages = get_lang(tags["language"])
                if languages==None:    
                    if "title" in tags:
                        languages = get_lang(tags["title"])
                if languages==None:    
                    if  "IAS1" in tags:
                        languages = get_lang(tags["IAS1"])
                if languages==None:    
                    if  "IAS2" in tags:
                        languages = get_lang(tags["IAS2"])
            if languages==None:    
                languages = ""



            ct=p["codec_type"]
            sm[ct] = p["codec_name"]

            if ct=="video":
                sm["res"] = [p["width"], p["height"]]
                if "duration" in format:
                    sm["duration"] = int(float(format["duration"])//60)
                elif "duration" in p:
                    sm["duration"] = int(float(p["duration"])//60)
            elif ct=="audio":
                sm["sample_rate"] = p["sample_rate"]
                if "channel_layout" in p:
                    sm["channel_layout"] = p["channel_layout"]
                sm["aud_langs"].append(languages)
            elif ct=="subtitle":
                sm["sub_langs"].append(languages)

        simple_movie_props[movie] = sm

    with open(f"{lang_path}/processed_movie_database.js","w") as f:
        f.write("processed_movie_database =" + json.dumps(simple_movie_props))



if False:
    print("list films")
    gen_movie_files(root_movies)   

print("fetching from imdb")
fetch_movies_imdb()
print("ffprobing")
generate_movie_ffprobes()        
print("gen posters")
get_posters(posters_path)
print("gen thumbs")
make_thumbs(posters_path, thumbs_path)

for file in glob.glob("./static/*"):
    shutil.copy(file, out_dir)
print("gen post processed database")
generate_processed_movie_database()
