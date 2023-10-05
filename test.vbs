Dim cam ' "The" Camera object
Set cam = CreateObject("MaxIm.CCDCamera")
cam.LinkEnabled = True

if Not cam.LinkEnabled Then
   wscript.echo "Failed to start camera."
   Quit
End If

wscript.echo "Camera is ready, Exposing."

cam.Expose 1, 1, 0

Do While Not cam.ImageReady
Loop

cam.SaveImage "Script.fit"
wscript.echo "Exposure is done, Image saved as Script.fit"