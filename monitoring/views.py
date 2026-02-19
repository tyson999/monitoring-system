from django.shortcuts import render, redirect
from openpyxl import Workbook 
from django.http import HttpResponse, JsonResponse
import pandas as pd 
import requests
from django.http import HttpResponse
import io, os
from django.conf import settings

def check_single_url(request):
    
    url = request.GET.get("url")
    
    if not url:
        return JsonResponse({"error": "No URL provided"}, status=400)
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
        
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code==200:
            return JsonResponse({"status":"Active"})
        else:
            return JsonResponse({
                "status": "Inactive",
                "code": response.status_code
            })
            
    except requests.exceptions.RequestException:
        return JsonResponse({"status": "Inactive"})

def status_page(request):
    results = request.session.get("results", [])
    
    total_count = len(results)
    active_count = sum(1 for r in results if r["status"] == "Active")
    inactive_count = sum(1 for r in results if r["status"] == "Inactive")


    return render(request, "status_page.html", {
        "results": results,
        "total_count": total_count,
        "active_count": active_count,
        "inactive_count": inactive_count,
    })
    


def welcome(request):
    return render(request, 'welcome.html')

def select_source(request):
    return render(request, 'select_source.html')

def upload_excel(request):

    if request.method == "GET":
        return render(request, "upload_excel.html")

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return render(request, "upload_excel.html", {
                "error": "Please select a file."
            })

        try:
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_name = excel_file.sheet_names
        except Exception as e:
            return render(request, "upload_excel.html", {
                "error": f"Error reading Excel file: {str(e)}"
            })

        possible_names = ["url", "website", "domain", "link"]
        all_urls = []

        
        for sheet_name in excel_file.sheet_names:
            df = excel_file.parse(sheet_name)

            if df.empty:
                continue

            
            df.columns = df.columns.str.lower().str.strip()

            url_column = None

            
            for name in possible_names:
                if name in df.columns:
                    url_column = name
                    break

            
            if not url_column:
                for col in df.columns:
                    if any(name in col for name in possible_names):
                        url_column = col
                        break

            if url_column:
                urls = df[url_column].dropna().astype(str).tolist()
                all_urls.extend(urls)

        if not all_urls:
            return render(request, "upload_excel.html", {
                "error": "No valid URL column found in any sheet."
            })

        results = []

        for url in all_urls:

            url = url.strip()

            if not url:
                continue

            if not url.startswith(("http://", "https://")):
                url = "http://" + url
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0 Safari/537.36",
                "Accept" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            }

            try:
                response = requests.get(url, timeout=20, headers=headers,allow_redirects=True)

                if response.status_code  < 400:
                    status = "Active"
                else:
                    status = f"Inactive ({response.status_code})"

            except requests.exceptions.RequestException:
                status = "Inactive"

            results.append({
                "url": url,
                "status": status
            })

        
        request.session["results"] = results
        request.session.modified = True

        return redirect("status_page")

from io import BytesIO


def google_sheet_input(request):
    
    if request.method == "GET":
        return render(request, "google_sheet_input.html")

    if request.method == "POST":

        sheet_url = request.POST.get("sheet_url")
        selected_sheet = request.POST.get("selected_sheet")
        

        if not sheet_url:
            return render(request, "google_sheet_input.html", {
                "error": "Please enter a Google Sheet link."
            })
            
        if not selected_sheet:
    
            try:
                sheet_id = sheet_url.split("/d/")[1].split("/")[0]
                export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(export_url, headers=headers, timeout=20)
                response.raise_for_status()

                excel_data = BytesIO(response.content)
                excel_file = pd.ExcelFile(excel_data)

                sheet_names = excel_file.sheet_names

                return render(request, "google_sheet_input.html", {
                    "sheet_url": sheet_url,
                    "sheet_names": sheet_names
                })

            except Exception as e:
                return render(request, "google_sheet_input.html", {
                    "error": f"Error reading Google Sheet: {str(e)}"
                })

        request.session["sheet_url"] = sheet_url
        request.session["selected_sheet"] = selected_sheet
               
        return redirect("processing_page")
    
def processing_page(request):
    return render(request, "processing_page.html")
    
  
def results_page(request):
    results = request.session.get("results",[])
    return render(request, "results.html", {"results": results})

def download_excel(request):
    
    results = request.session.get("results", [])
    selected_sheet = request.session.get("sheet")
    
    print("DOWNLOADING FOR:" , selected_sheet)
    
    if selected_sheet:
        results = [
            r for r in results
            if r["sheet_name"] == selected_sheet
        ]

    
    active_urls = [
        r["url"] for r in results
        if r["status"] == "Active"
    ]

    df = pd.DataFrame(active_urls, columns=["URL"])

    response = HttpResponse(content_type="text/csv")
    filename = f"active_{selected_sheet or 'all'}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    df.to_csv(response, index=False)

    return response
    
    
def download_inactive(request):
    results = request.session.get("results", [])
    selected_sheet = request.session.get("sheet")

    
    if selected_sheet:
        results = [
            r for r in results
            if r["sheet_name"] == selected_sheet
        ]

    
    inactive_urls = [
        r["url"] for r in results
        if r["status"].startswith("Inactive")
    ]

    df = pd.DataFrame(inactive_urls, columns=["URL"])

    response = HttpResponse(content_type="text/csv")
    filename = f"inactive_{selected_sheet or 'all'}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    df.to_csv(response, index=False)

    return response

def run_processing(request):
    
    sheet_url = request.session.get("sheet_url")
    selected_sheet = request.session.get("selected_sheet")

    if not sheet_url or not selected_sheet:
        return redirect("google_sheet_input")

    try:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(export_url, headers=headers, timeout=10)
        response.raise_for_status()

        excel_data = BytesIO(response.content)
        excel_file = pd.ExcelFile(excel_data)

        results = []

        if selected_sheet == "ALL":
            sheets_to_process = excel_file.sheet_names
        else:
            sheets_to_process = [selected_sheet]

        for sheet in sheets_to_process:

            df = excel_file.parse(sheet)

            if df.empty:
                continue

            df.columns = df.columns.astype(str).str.lower().str.strip()

            url_column = None
            for col in df.columns:
                if "url" in col or "link" in col or "website" in col or "sites" in col:
                    url_column = col
                    break

            if not url_column:
                continue

            urls = df[url_column].dropna().astype(str).tolist()

            for url in urls:

                url = url.strip()

                if "." not in url:
                    continue

                if not url.startswith(("http://", "https://")):
                    url = "http://" + url

                try:
                    r = requests.head(url, headers=headers, timeout=8, allow_redirects=True)

                    if r.status_code >= 400:
                        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)

                    if 200 <= r.status_code < 400 or r.status_code == 403:
                        status = "Active"
                    else:
                        status = "Inactive"

                except requests.exceptions.RequestException:
                    status = "Inactive"

                
                results.append({
                    "sheet_name": sheet,
                    "url": url,
                    "status": status
                })

        request.session["results"] = results

    except Exception:
        return redirect("google_sheet_input")

    return redirect("status_page")

        
        

        
   
