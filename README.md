# image to text app
About
Developer: Chadee Fouad - MyWorkDropBox@gmail.com
Development Date: Aug 2024.

Credit for wallpaper image goes to: https://wallpapercave.com/

Purpose:
This can be used as a generic app for splitting large pdfs file into a seperate pdf for each page.

In addition this app is also designed to solve a difficult problem for a friend:
Currently Product Delivery Orders come as a large scanned PDF file. The follwing is required on this file:
1- Create a seperate file for each page.
2- Use AI Machine vision to read the Delivery Order Number in the pdf.
3- Rename the file to be the same as the order number in the scanned image so that it's easy to search for the Delivery Order when needed.
4- If the AI fails to detect the Delivery Order Number, name the file with its page number for further investigation.
5- Create a zip file which contains the original file plus all the extracted files.

This app does that, which saves an enormous time and reduces errors as opposed to doing it manually for hundreds of files.

Key Challenges:
1- Dynamically detecting the area of the Delivery Order Number within the scanned image.
2- Bad printing quality causing some parts of the number to be missing, which confuses AI.
3- Numbers being treated as text. e.g. o vs. 0 or I vs. 1.
4- Sometimes there's handwriting with a pen over the numbers which confuses the detection algorithm
5- Different image colors.

To Address Those Challenges:
1- I've used various filters in order to find the best quality. Filters include pure black & white, greyscale, etc.
2- Several error detection and correction techniques to ensure that the right pattern is being captured.