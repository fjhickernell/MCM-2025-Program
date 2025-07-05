import os
import pandas as pd
import urllib.parse
import requests
import re

from config import *


pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)


def save_dfs(dfs, interimdir, filedes):
    """Save each schedule DataFrame in a dictionary to CSV"""
    for key, df in dfs.items():
        #print(df.head(10))
        csv_file = os.path.join(interimdir, f"{key}_{filedes}.csv")
        df.to_csv(csv_file, index=False)
        print("Output: ",  f"{csv_file}")


def clean_df(df):
    """Remove all columns and rows with only NaN values."""
    df = df.dropna(axis=1, how='all')
    df = df.dropna(axis=0, how='all')
    # for each str column, remove leading and trailing whitespace
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    return df.copy(deep=True)


def read_gsheet(sheet_id, sheet_name, indir, out_csv, always_download=True):
    """Read a Google Sheet into a DataFrame, downloading only if the local CSV does not exist."""
    csv_path = os.path.join(indir, out_csv)
    
    # Check if the file exists and should be downloaded
    if (not always_download) and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        df = pd.read_csv(url)
        df = clean_df(df)
        df.to_csv(csv_path, index=False, quoting=1)
    
    return df

def download_file(url, output_dir, session_id):
    """Download a file from a URL and save it in output_dir with session_id as the filename."""
    if not url or not isinstance(url, str) or not url.startswith("http"):
        print(f"Invalid URL for session {session_id}: {url}")
        return
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        filename = f"{session_id}.tex"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Failed to download {url} for session {session_id}: {e}")

def gdrive_direct_download(url):
    """Convert a Google Drive share/view URL to a direct download URL if possible."""
    patterns = [
        r"drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/uc\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/uc\?export=download&id=([a-zA-Z0-9_-]+)"
    ]
    
    for pat in patterns:
        match = re.search(pat, url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    return url  # Return original if not matched


def read_google_sheets(sheets, indir):
    """Read all sheets into a dictionary of DataFrames, selecting only needed columns."""
    dfs = {}
    
    for key, meta in sheets.items():
        df = read_gsheet(
            sheet_id=meta["sheet_id"],
            sheet_name=meta["sheet_name"],
            indir=indir,
            out_csv=f"{key}.csv"
        )
        
        if meta["columns"] is not None:
            df = df[meta["columns"]]
        
        dfs[key] = df.copy(deep=True)
    
    return dfs

def clean_tex_content(text):
    """
    Clean and fix common spelling, grammar, and formatting issues in LaTeX content.
    
    Args:
        text (str): Input LaTeX text to clean
        
    Returns:
        str: Cleaned LaTeX text with fixes applied
    """
    if not isinstance(text, str):
        return text
    
    # Define problematic LaTeX expressions to remove
    bad_s = "{}% [6] special session. Leave this field empty for contributed talks. "
    bad_s2 = "% Insert the title of the special session if you were invited to give a talk in a special session."
    
    # Apply text cleanup fixes
    cleaned_text = (text
        # Spelling and grammar corrections
        .replace("Stong order", "Strong order")
        .replace("Inverstigating", "Investigating")
        .replace("Ellip- tic", "Elliptic")
        .replace("constrast", "contrast")
        .replace("Lebesque", "Lebesgue")
        .replace("Sou-Cheng T.  Choi", "Sou-Cheng T. Choi")
        .replace("et al ", "et al. ")
        .replace("This goal of this talk", "The goal of this talk")  
        .replace("we are interested the behaviour", "we are interested in the behaviour")
        .replace("Hyper-parameters", "Hyperparameters").replace("hyperparamters", "hyperparameters")
        .replace("called adapted Wasserstein distance", "called the adapted Wasserstein distance")
        .replace("high accuracy solutions", "high-accuracy solutions") 
        .replace("low accuracy solutions", "low-accuracy solutions")
        .replace("Liklihood ", "Likelihood").replace("liklihood", "likelihood")
        .replace("Goal Oriented Sensor Placement", "Goal-Oriented Sensor Placement")
        .replace("progress on them have", "progress on them has")
        .replace("we consider the how Monte", " we consider how Monte")
        .replace(" stein ", " Stein ")
        .replace("boundary preserving discretization scheme", "boundary-preserving discretization scheme")
        .replace("has strong convergence order", "has a strong convergence order")
        .replace("Furthermore it ",  "Furthermore, it ")
        .replace("In this talk we", "In this talk, we").replace("in this talk we", "in this talk, we").replace("In this paper, We ", "In this paper, we ").replace("In this talk I", "In this talk, I")
        .replace("In this work we ", "In this work, we ")
        .replace("with discontinuous drift coefficient", "with a discontinuous drift coefficient")
        .replace("i.e. ", "i.e., ")
        .replace("e.g. ", "e.g., ")
        .replace("has convergence order", "has a convergence order")
        .replace("are assumed be random ", "are assumed to be random ")
        .replace("quantitites", "quantities")
        .replace(" low precision calculations", " low-precision calculations")
        .replace("antipication", "anticipation")
        .replace("First we consider ", "First, we consider ")
        .replace("worst case error", "worst-case error")
        .replace("analysis .", "analysis.")
        .replace("consists in", "consists of")
        .replace("raisonnable assumptions...", "reasonable assumptions")
        .replace("first order derivative", "first-order derivative")
        .replace("analysis typically assume ", "analysis typically assumes ")
        .replace("methods, which requires", "methods, which require")
        .replace("Parallel computations for Metropolis Markov chains Based on Picard maps", "Parallel computations for Metropolis Markov chains based on Picard maps")
        .replace("representation to the solutions", "representation of the solutions")
        .replace("have lead to", "have led to")
        .replace("cost effective way", "cost-effective way")
        .replace("algorithms in benchmark non-convex", "algorithms in benchmarking non-convex problems")
        .replace("appproach", "approach")
        .replace("models facilitates", "models facilitate")
        .replace("hit and run approach", "hit-and-run approach")
        .replace("adaption", "adaptation")
        .replace("simultaneous collect ", "simultaneously collect ")
        .replace("proposals that improves", "proposals that improve")
        .replace("applications to many areas", "applications in many areas")
        .replace("hyper cube", "hypercube")
        .replace("conditon", "condition")
        .replace("occuring", "occurring")
        .replace("algorithm allows to understand", "algorithm allows us to understand")
        .replace("in addition to not be defined ", "in addition to not being defined ")
        .replace(" which acts a bridge", " which acts as a bridge")
        .replace("equidsipersion", "equidispersion")
        .replace("a average", "an average")
        .replace("Compuational", "Computational")
        .replace("good agreements", "good agreement")
        .replace("first order and second order numerical integrator", "first-order and second-order numerical integrators")
        .replace("array of application ", "array of applications ")
        .replace("well defined sets", "well-defined sets")
        .replace("simulations divide into", "simulations are divided into")
        .replace("non- linear", "nonlinear").replace("non linear", "nonlinear")
        .replace("solusions", "solutions")        
        .replace("management(In russian) .", "management (in Russian).")
        .replace("low discrepancy sequences", "low-discrepancy sequences")
        .replace(" india." , " India.")
        .replace("ditribution", "distribution")
        .replace("Our seems to be the first result", "Our result seems to be the first")
        .replace("we believe might be applicable ", "we believe they might be applicable ")
        .replace("This formulation allows for accurately sampling the Bayesian posterior", "This formulation allows for accurate sampling of the Bayesian posterior")
        .replace("a interacting", "an interacting")
        .replace("non ergodic", "non-ergodic")
        .replace("To achieve an unbiasedness", "To achieve unbiasedness")
        .replace("high dimensional regime", "high-dimensional regime")
        .replace("high dimensional case", "high-dimensional case")
        .replace("4th order integrator", "4th-order integrator")
        .replace("user defined threshold", "user-defined threshold")
        .replace("user requested residual", "user-requested residual")
        .replace("high energy physics", "high-energy physics")
        .replace("Sciencess", "Sciences")
        .replace("arbitrary amount of bits", "arbitrary number of bits")
        .replace('Boltzmann equations” work”', "Boltzmann equations ``work''")
        .replace("“particle-in-cell”", "``particle-in-cell''")

        # Capitalization fixes for technical terms
        .replace("monte carlo", "Monte Carlo")
        .replace("quasi-monte carlo", "quasi-Monte Carlo")
        .replace("hamiltonian", "Hamiltonian")
        .replace("markov", "Markov")
        .replace("Acta numerica", "Acta Numerica")
        .replace("Functiones and Approximatio", "Functiones et Approximatio")
        .replace("Physics letters B", "Physics Letters B")
        .replace("Oxford university press", "Oxford University Press")
        .replace("Nature communications", "Nature Communications")
        .replace("bayesian", "Bayesian")
        .replace("langevin", "Langevin")
        .replace("brownian", "Brownian")
        
        # Grammar fixes (duplicated words)
        .replace("the the ", "the ")
        .replace("that that ", "that ")
        .replace("approach approach ", "approach ")
        
        # Institution name cleanup
        .replace("(KAUST) King Abdullah University of Science and Technology", "King Abdullah University of Science and Technology")
        
        # Date/time formatting
        .replace("Fri, Aug 1 11:30-12:30—", "Fri, Aug 1 11:30-12:30")
        .replace("09:00---11:00— ", "09:00--11:00")
        
        # LaTeX math notation fixes
        .replace("$\\cL_p$", "$\\mathcal{L}_p$")
        .replace("\\KSD", "\\mathsf{KSD}")
        .replace('Φ', '$\Phi$')
        
        # Special character and symbol fixes
        .replace("–", "--")  # unicode dash to LaTeX dash
        #.replace(" &", " \\&")  # escape ampersand
        
        # Remove problematic LaTeX comments
        .replace(bad_s, "")
        .replace(bad_s2, "")
        
        # Whitespace cleanup
        .replace("\t", " ")  # replace tabs with spaces
        .replace("\r", "")   # remove carriage returns
    )
    
    # Fix malformed href commands using regex
    import re
    # Fix incomplete \href{url} without display text - add the URL as display text
    cleaned_text = re.sub(r'\\href\{([^}]+)\}(?!\{)', r'\\href{\1}{\1}', cleaned_text)
    
    # Continue with remaining replacements
    cleaned_text = (cleaned_text
        # Standardize British to American spelling for technical terms
        #.replace("behaviour", "behavior")
        #.replace("optimisation", "optimization")
        #.replace("modelling", "modeling")
        #.replace("endeavour", "endeavor")
        #.replace("analyse", "analyze")
        #.replace("analysed", "analyzed")
        #.replace("analysing", "analyzing")
        #.replace("minimise", "minimize")
        #.replace("colour", "color")
     
        # Vowels with accents
        .replace("á", "\\'a")
        .replace("à", "\\`a")
        .replace("â", "\\^a")
        .replace("ä", "\\\"a")
        .replace("å", "{\\aa}")
        .replace("ã", "\\~a")
        .replace("Á", "\\'A")
        .replace("À", "\\`A")
        .replace("Â", "\\^A")
        .replace("Ä", "\\\"A")
        .replace("Å", "{\\AA}")
        .replace("Ã", "\\~A")
        .replace("é", "\\'e")
        .replace("è", "\\`e")
        .replace("ê", "\\^e")
        .replace("ë", "\\\"e")
        .replace("É", "\\'E")
        .replace("È", "\\`E")
        .replace("Ê", "\\^E")
        .replace("Ë", "\\\"E")
        .replace("í", "\\'i")
        .replace("ì", "\\`i")
        .replace("î", "\\^i")
        .replace("ï", "\\\"i")
        .replace("Í", "\\'I")
        .replace("Ì", "\\`I")
        .replace("Î", "\\^I")
        .replace("Ï", "\\\"I")
        .replace("ó", "\\'o")
        .replace("ò", "\\`o")
        .replace("ô", "\\^o")
        .replace("ö", "\\\"o")
        .replace("õ", "\\~o")
        .replace("ø", "{\\o}")
        .replace("Ó", "\\'O")
        .replace("Ò", "\\`O")
        .replace("Ô", "\\^O")
        .replace("Ö", "\\\"O")
        .replace("Õ", "\\~O")
        .replace("Ø", "{\\O}")
        .replace("ú", "\\'u")
        .replace("ù", "\\`u")
        .replace("û", "\\^u")
        .replace("ü", "\\\"u")
        .replace("Ú", "\\'U")
        .replace("Ù", "\\`U")
        .replace("Û", "\\^U")
        .replace("Ü", "\\\"U")
        .replace("ý", "\\'y")
        .replace("ÿ", "\\\"y")
        .replace("Ý", "\\'Y")
        .replace("Ÿ", "\\\"Y")
        # Special characters
        .replace("ç", "\\c{c}")
        .replace("Ç", "\\c{C}")
        .replace("ñ", "\\~n")
        .replace("Ñ", "\\~N")
        .replace("ß", "{\\ss}")
        # Eastern European characters
        .replace("č", "\\v{c}")
        .replace("Č", "\\v{C}")
        .replace("ć", "\\'c")
        .replace("Ć", "\\'C")
        .replace("š", "\\v{s}")
        .replace("Š", "\\v{S}")
        .replace("ž", "\\v{z}")
        .replace("Ž", "\\v{Z}")
        .replace("ř", "\\v{r}")
        .replace("Ř", "\\v{R}")
        .replace("ě", "\\v{e}")
        .replace("Ě", "\\v{E}")
        .replace("ů", "\\r{u}")
        .replace("Ů", "\\r{U}")
        .replace("đ", "\\dj{}")
        .replace("Đ", "\\DJ{}")
        .replace("ł", "{\\l}")
        .replace("Ł", "{\\L}")
    )
    
    return cleaned_text