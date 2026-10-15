import json
import pandas as pd
from pathlib import Path
from Variables import PATH_JSON, PATH_CSV, PATH_MEAN, ESTIMATED_NBH_POP, ESTIMATED_NBH_W, DATA_MAIN_NBH

class Generate_Ceps:
    def centroid(self,lats, lons, trim=0.05):
        lats_i = list(map(float,lats)); lons_i = list(map(float,lons))
        lats_s = sorted(lats_i); lons_s = sorted(lons_i)
        
        n = len(lats_s)
        k = int(n * trim)
        Lats = sum(lats_s[k:n-k]) / (n - 2*k)
        Lons = sum(lons_s[k:n-k]) / (n - 2*k)
        return (Lats,Lons)
            
    def generate_central_cep(self):
        pasta = Path("../cepsjf")
        saida = Path(PATH_JSON)
        
        consolidado = {}
        
        for arquivo in pasta.rglob("*.json"):
            cep = arquivo.stem
            if not (cep.isdigit() and len(cep) == 8):
                continue
        
            with arquivo.open(encoding="utf-8") as f:
                dados = json.load(f)
                dados.pop("cep", None)
        
            consolidado[cep] = dados
        
        with saida.open("w", encoding="utf-8") as f:
            json.dump(consolidado, f, ensure_ascii=False, indent=2)
    
    
    def get_mean_cep(self):
        self.generate_central_cep()
        arquivo = Path(PATH_JSON)
        output = Path(PATH_MEAN)
        
        with arquivo.open(encoding="utf-8") as f:
            dados = json.load(f)
            
        df_ceps_jf = pd.read_csv(PATH_CSV)
    
        nbhs = df_ceps_jf[df_ceps_jf.columns[0]]
        min_ceps = df_ceps_jf[df_ceps_jf.columns[1]]
        max_ceps = df_ceps_jf[df_ceps_jf.columns[2]]
    
        nbh_mean_relationship = {}
        for i in range(df_ceps_jf.shape[0]):    
            nbh = str(nbhs[i]); min_cep = min_ceps[i].item(); max_cep = max_ceps[i].item(); #.item() converte a Serie de elemento único para numero(int, float,etc...)
            lats = []; longs= []

            dif = max_cep - min_cep
            it=0
            while(it<=dif):
                json_at = dados.get(str(min_cep+it))
                if json_at is None:
                    it+=1
                    continue
                        
                lats.append(json_at['latitude'])
                longs.append(json_at['longitude'])
                it+=1
    
            if len(lats)>0 and len(longs)>0:
                mean_lat, mean_long = self.centroid(lats,longs)
                nbh_mean_relationship[nbh] = {
                    'latitude': mean_lat, 'longitude': mean_long,
                    'cmin':min_cep, 'cmax': max_cep,
                    'w': DATA_MAIN_NBH[nbh]['peso'] if nbh in DATA_MAIN_NBH else ESTIMATED_NBH_W
                }
                with output.open("w", encoding="utf-8") as f:
                    json.dump(nbh_mean_relationship, f, ensure_ascii=False, indent=2)
                        
        return nbh_mean_relationship


gen = Generate_Ceps()
gen.get_mean_cep()