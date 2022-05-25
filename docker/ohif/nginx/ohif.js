window.config = {
    // default: '/'
    routerBasename: '/',
    extensions: [],
    showStudyList: true,
    filterQueryParam: false,
    servers: {
      dicomWeb: [
        {
          name: 'Orthanc',
          wadoUriRoot: '/orthanc/wado',
          qidoRoot: '/orthanc/dicom-web',
          wadoRoot: '/orthanc/dicom-web',
          imageRendering: 'wadors',
          thumbnailRendering: 'wadors',
          enableStudyLazyLoad: true,
          supportsFuzzyMatching: true,
        },
      ],
    },
    maxConcurrentMetadataRequests: 5,
  };