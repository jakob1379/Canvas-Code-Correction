# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [1.8.0](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.7.0...v1.8.0) (2021-10-15)


### Features

* reads max subprocesses from config ([94b9b30](https://github.com/jakob1379/Canvas-Code-Correction/commits/94b9b30045ff1085824606d1b2a0ced29e5c9c9e))
* rewritten unzip script in python ([7dbbf10](https://github.com/jakob1379/Canvas-Code-Correction/commits/7dbbf105aa8805f0198f714cb1a3952f10a1be5e))
* rewritten unzip script in python ([ea9ec8c](https://github.com/jakob1379/Canvas-Code-Correction/commits/ea9ec8c24fd69655c3a2a33156c8a5223b8f762b))
* rewrote delete_submissions to python ([cc96234](https://github.com/jakob1379/Canvas-Code-Correction/commits/cc96234e25e7cb4ac2fdb9f00834421d074b135f))
* rewrote delete_submissions to python ([5775d65](https://github.com/jakob1379/Canvas-Code-Correction/commits/5775d658f092f1f34223108a19fc8b44a4098a08))


### Bug Fixes

* added default values to config.getfloat ([5225690](https://github.com/jakob1379/Canvas-Code-Correction/commits/5225690663c1117b8c8f74f26306b553a8180041))
* copies as archice and dereference links ([167c6a0](https://github.com/jakob1379/Canvas-Code-Correction/commits/167c6a0de23eca20961332305a7e096e39cf6ed0))
* find didn't find properly ([d500af6](https://github.com/jakob1379/Canvas-Code-Correction/commits/d500af68dd3202860bcb8afaf6634a1119073ad8))
* imrproved unpacking ([55c3865](https://github.com/jakob1379/Canvas-Code-Correction/commits/55c3865d136fc1e2c01e7ee7182165a48bc71548))
* now handles unwritable files properly ([e3a6ddd](https://github.com/jakob1379/Canvas-Code-Correction/commits/e3a6ddd20ea17abf844dbc9095e314d0444b948c))
* protection for config nooptions errors ([8f57706](https://github.com/jakob1379/Canvas-Code-Correction/commits/8f577060ca137b479411b92d0b699f788209a98b))
* secure settings ([d1c6e70](https://github.com/jakob1379/Canvas-Code-Correction/commits/d1c6e704216e022e9a2ac84b38075ea8a84bba92))
* updated md5sum to stream byte data for larger files ([e194201](https://github.com/jakob1379/Canvas-Code-Correction/commits/e194201b1c63a37a0c016ac0965f1718ed9fcdca))
* updated unzipping number of positional args ([3a13f36](https://github.com/jakob1379/Canvas-Code-Correction/commits/3a13f36fe05069ecc6f84a97c8d5818601c69a35))

## [1.7.0](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.6.3...v1.7.0) (2021-10-05)


### Features

* added cache options and improved plotting ([09bd817](https://github.com/jakob1379/Canvas-Code-Correction/commits/09bd8170089258890493a78b32dfa464092b588e))
* added clause checking for attempts allowed violation ([a247532](https://github.com/jakob1379/Canvas-Code-Correction/commits/a2475328fe50867281debbefcf0bf87301a903a3))
* download now saves data for later use ([fe8e587](https://github.com/jakob1379/Canvas-Code-Correction/commits/fe8e5873d5dd9a60f8a86468c2a5f55f5cb5f992))


### Bug Fixes

* added delay for communication with absalon to prevent 504 ([2e5253a](https://github.com/jakob1379/Canvas-Code-Correction/commits/2e5253aa6f1a72775e442cf94c5482d78b8979ee))
* continues when encountering undeletable files ([32e0eed](https://github.com/jakob1379/Canvas-Code-Correction/commits/32e0eed3f513fc9aa3c0fac268740ffe8bc57af1))
* didn't spawm process if max was reached, thus skipping many ([1d763cc](https://github.com/jakob1379/Canvas-Code-Correction/commits/1d763cc4fffe19c9fdfb8666e7994f216180ba8d))
* hopefully fixed issue with permission denied files ([b636ea1](https://github.com/jakob1379/Canvas-Code-Correction/commits/b636ea17430f77d64855f03c6cf8ff4158dd237e))
* implemented a simple wait for older systems ([6e0d71a](https://github.com/jakob1379/Canvas-Code-Correction/commits/6e0d71a494692ebf777c4cb965b877dc1ff73e14))
* improved path handling when downloading from url ([868f94b](https://github.com/jakob1379/Canvas-Code-Correction/commits/868f94b64cec63312b66508af83585c2d4bb5c0e))
* secured rm for breaking if it meets weird permissions ([c460b2c](https://github.com/jakob1379/Canvas-Code-Correction/commits/c460b2cf5c78bde7ebeb11c0f43a798faf38e8f7))

### [1.6.3](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.6.2...v1.6.3) (2021-10-01)

### [1.6.2](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.6.1...v1.6.2) (2021-10-01)


### Bug Fixes

* using /usr/rm instead of find to delete ([a222f20](https://github.com/jakob1379/Canvas-Code-Correction/commits/a222f20b36c2f97eed025131411c1fcd786af0c3))

### [1.6.1](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.6.0...v1.6.1) (2021-10-01)

## [1.6.0](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.5.3...v1.6.0) (2021-10-01)


### Features

* implemented parallel code correction ([d21f7d7](https://github.com/jakob1379/Canvas-Code-Correction/commits/d21f7d733f587d7254210a8b9066f30ebca92a5e))
* moved bcolors to own module with new methods for easy format ([83bfc6f](https://github.com/jakob1379/Canvas-Code-Correction/commits/83bfc6fcc00c5fb4a71830dce03bb58ab45618ef))


### Bug Fixes

* fix for correct index in submissions ([705d970](https://github.com/jakob1379/Canvas-Code-Correction/commits/705d970e918223ef1cb0e9785465084f47c909dc))
* more robust clearing of submissions ([03c7a45](https://github.com/jakob1379/Canvas-Code-Correction/commits/03c7a459185504d612098a689763fe0e7eac35d6))
* restricted depth of find ([ed29510](https://github.com/jakob1379/Canvas-Code-Correction/commits/ed29510c9a2946515987279745eebbb0718c697a))

### [1.5.3](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.5.2...v1.5.3) (2021-09-26)

### [1.5.2](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.5.1...v1.5.2) (2021-09-26)


### Bug Fixes

* checking md5sum ([3c354c4](https://github.com/jakob1379/Canvas-Code-Correction/commits/3c354c4b0b30dfc47dc4ecc65e8b4c763e6473fe))
* counting elements of array ([2deff9b](https://github.com/jakob1379/Canvas-Code-Correction/commits/2deff9b62f96a8847a2cc58c704d3367c95165e1))

### [1.5.1](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.5.0...v1.5.1) (2021-09-25)

## [1.5.0](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.4.4...v1.5.0) (2021-09-24)


### Features

* added timeout for submissions and init-config ([65c8d82](https://github.com/jakob1379/Canvas-Code-Correction/commits/65c8d82ad3e0ae684d303cc6c3ce5da3ca0b13c5))
* added timeout for submissions and init-config ([15257e5](https://github.com/jakob1379/Canvas-Code-Correction/commits/15257e5b73d7bdfe10489fab05f60a29f25f44d7))
* feature: added config variables to shell, so main.sh can use them ([448e788](https://github.com/jakob1379/Canvas-Code-Correction/commits/448e78899d304fb432bad06cba3649b42fbd4fd9))


### Bug Fixes

* bad string concat ([7259135](https://github.com/jakob1379/Canvas-Code-Correction/commits/7259135e76df84823c7b0c44cfccbaab0c204165))
* changed behaviour when reaching timeout ([d145363](https://github.com/jakob1379/Canvas-Code-Correction/commits/d1453637865bb4cfea9beac2acca7b4dca896972))
* changed behaviour when reaching timeout ([ff10220](https://github.com/jakob1379/Canvas-Code-Correction/commits/ff102204d6a2dcfd9a0eab088f7c6c7f0a4a2b82))
* changed logic to save exit_code ([7ec319f](https://github.com/jakob1379/Canvas-Code-Correction/commits/7ec319ff4ba33140ab6ac044b6ef0f4ddd6aea6c))
* corrected boolean comparison ([f9105c9](https://github.com/jakob1379/Canvas-Code-Correction/commits/f9105c9d90be9b6164e358197c7dd52901c49efe))
* didn't save basename ([dd7707a](https://github.com/jakob1379/Canvas-Code-Correction/commits/dd7707a15215487ed54302b24a03d40f475cb8f5))
* echo test-message ([0ed9c32](https://github.com/jakob1379/Canvas-Code-Correction/commits/0ed9c3299650365db61cfc393475c2a4fa80b17a))
* fixed percent formatting ([793609c](https://github.com/jakob1379/Canvas-Code-Correction/commits/793609c4ec493099d1726fd7c6240f8051b8d3d1))
* generalized plotting further and added interactive session ([90ae7df](https://github.com/jakob1379/Canvas-Code-Correction/commits/90ae7dfbe9c2a4199551c28c16db2dc8c70da017))
* minor edit ([35595a5](https://github.com/jakob1379/Canvas-Code-Correction/commits/35595a5f898a86a39eac814576d37026e0b680c7))
* minor edit ([8f8dc8f](https://github.com/jakob1379/Canvas-Code-Correction/commits/8f8dc8f8e4ee723adcdb8d883520a201a43eef4d))
* more testing ([b1ca8a5](https://github.com/jakob1379/Canvas-Code-Correction/commits/b1ca8a5b106ecc5e9049f4ec662e743a55e74923))
* more testing ([2f01fec](https://github.com/jakob1379/Canvas-Code-Correction/commits/2f01fec6756513259773d7be63c7da259a205b86))
* path joining made systemless ([27ca0ec](https://github.com/jakob1379/Canvas-Code-Correction/commits/27ca0eccb1fb3d9464c0e218e32f3935bb0fbdf7))
* removed stupid space ([1dabd6e](https://github.com/jakob1379/Canvas-Code-Correction/commits/1dabd6ecc54f5fe0329d49929401115fe4a0132c))
* removed testing lines and corrected timeout message ([91a2f35](https://github.com/jakob1379/Canvas-Code-Correction/commits/91a2f3561c47004bd30f0c4dbddfd1b1da65f838))
* simplified printings ([256cdcf](https://github.com/jakob1379/Canvas-Code-Correction/commits/256cdcf4fcf454f9b105d2a9b989d572f1996d17))
* try with altered exit_code writing ([de32489](https://github.com/jakob1379/Canvas-Code-Correction/commits/de32489549a67d861130c3753da79bf842d6e587))

### [1.4.4](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.4.3...v1.4.4) (2021-09-16)


### Bug Fixes

* changed to correct lookup for points needed ([e91becf](https://github.com/jakob1379/Canvas-Code-Correction/commits/e91becf916affb6af4df9d4fc9f5e91baaa30db3))
* fixed percent formatting ([c6ee8b5](https://github.com/jakob1379/Canvas-Code-Correction/commits/c6ee8b552938d537efe01281b50c06ba217e49c4))

### [1.4.3](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.4.2...v1.4.3) (2021-09-15)


### Bug Fixes

* accounts for grading type percent ([eb83c7e](https://github.com/jakob1379/Canvas-Code-Correction/commits/eb83c7e0372767ff695e999998c67a0975e4a721))
* disabled parallel download as defaul ([2552e18](https://github.com/jakob1379/Canvas-Code-Correction/commits/2552e187668240ae23c6247a101f075b0096b576))
* passed wrong element to get_grade ([d15dc08](https://github.com/jakob1379/Canvas-Code-Correction/commits/d15dc08bd2d4fa96c404ffc924f67423b9cb12e3))
* writes output to terminal directly ([0e5e3b0](https://github.com/jakob1379/Canvas-Code-Correction/commits/0e5e3b030720c3535ad7bb9fafbd998d86485b05))

### [1.4.2](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.4.0...v1.4.2) (2021-09-15)


### Bug Fixes

* fixed bad unzipping ([feae67f](https://github.com/jakob1379/Canvas-Code-Correction/commits/feae67f94ab020af900e686591ee6d2d83120e99))

### [1.4.1](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.4.0...v1.4.1) (2021-09-15)

## [1.4.0](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.3.0...v1.4.0) (2021-09-15)


### Features

* changed name of main to ccc ([318da24](https://github.com/jakob1379/Canvas-Code-Correction/commits/318da244734bbd2917f09a59247f01d67f4dec1a))
* downloads and unpack directly in folder ([e80907b](https://github.com/jakob1379/Canvas-Code-Correction/commits/e80907be0550fb05a47c4339db5236222ca483fa))
* randomizes order of correction to continue after breaking ([75bd6e0](https://github.com/jakob1379/Canvas-Code-Correction/commits/75bd6e0fe66ba05339553a7d7837dc7f8d202aff))
* updated plotting to use new df format ([420e99d](https://github.com/jakob1379/Canvas-Code-Correction/commits/420e99d79b00c23919277287b86cc179cab2b5f2))


### Bug Fixes

* added init tmp folder ([7c5dc82](https://github.com/jakob1379/Canvas-Code-Correction/commits/7c5dc82112341baab9e145428bf83beb73dc27fa))
* added package-lock.json ([6af0215](https://github.com/jakob1379/Canvas-Code-Correction/commits/6af02154384fee9327b17c46fd901b9b18bf36dd))
* does not download submissions without attachments ([ea9e035](https://github.com/jakob1379/Canvas-Code-Correction/commits/ea9e035d34a095de46c8ff7bfe62b910e5def3fd))
* download failed generalized more ([ae02889](https://github.com/jakob1379/Canvas-Code-Correction/commits/ae02889f900c269efdf1a78365fb7df9f452fe36))
* ignored package-lock.json ([131139d](https://github.com/jakob1379/Canvas-Code-Correction/commits/131139dcf1196aed8b8986e83615265688479e85))
* removed lock-file as it is not needed for online repo ([37ac21f](https://github.com/jakob1379/Canvas-Code-Correction/commits/37ac21f3f3654aef91e9aafe36162ee43c68f22d))
* removed unnecessary line ([84879d1](https://github.com/jakob1379/Canvas-Code-Correction/commits/84879d1e9981424e8e74faa300af06545ee1598e))

## [1.3.0](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.2.2...v1.3.0) (2021-09-09)


### Features

* added sandbox options ([0292451](https://github.com/jakob1379/Canvas-Code-Correction/commits/029245139e6750433c4b0cb8fc35fe347d5aea32))


### Bug Fixes

* quoted variable ([cfff352](https://github.com/jakob1379/Canvas-Code-Correction/commits/cfff35221a61da3ef118651499d6768a9fc7ea0f))
* requirements messages updated ([f8bcfcb](https://github.com/jakob1379/Canvas-Code-Correction/commits/f8bcfcbc1224ab3fbe32688194b4fd12c39b5663))
* unzip now moves content of single folder 1 up ([eb40bed](https://github.com/jakob1379/Canvas-Code-Correction/commits/eb40bed20fac0d459d9438becea1bcb90ffd7b8a))

### [1.2.2](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.2.0...v1.2.2) (2021-09-07)


### Bug Fixes

* removed unwanted files, added check for moss ([26c7773](https://github.com/jakob1379/Canvas-Code-Correction/commits/26c777383c7b1173c31634569fb25cff30c3cf57))

### [1.2.1](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.2.0...v1.2.1) (2021-09-07)


### Bug Fixes

* removed unwanted files, added check for moss ([26c7773](https://github.com/jakob1379/Canvas-Code-Correction/commits/26c777383c7b1173c31634569fb25cff30c3cf57))

## [1.2.0](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.1.4...v1.2.0) (2021-09-07)

### [1.1.4](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.1.0...v1.1.4) (2021-09-06)


### Bug Fixes

* added package.json ([97b99c0](https://github.com/jakob1379/Canvas-Code-Correction/commits/97b99c031c753b27c464dd00c7aaf07721a2b291))
* more changes ([3f7012c](https://github.com/jakob1379/Canvas-Code-Correction/commits/3f7012c1c8504d3a70f076447e85aa386b6c771a))
* removed unwanted files ([9378557](https://github.com/jakob1379/Canvas-Code-Correction/commits/9378557fb24973ff97c04e161fcd473c6a08ac89))

### [1.1.3](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.1.0...v1.1.3) (2021-09-06)


### Bug Fixes

* added package.json ([97b99c0](https://github.com/jakob1379/Canvas-Code-Correction/commits/97b99c031c753b27c464dd00c7aaf07721a2b291))
* more changes ([3f7012c](https://github.com/jakob1379/Canvas-Code-Correction/commits/3f7012c1c8504d3a70f076447e85aa386b6c771a))
* removed unwanted files ([9378557](https://github.com/jakob1379/Canvas-Code-Correction/commits/9378557fb24973ff97c04e161fcd473c6a08ac89))

### [1.1.2](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.1.0...v1.1.2) (2021-09-06)


### Bug Fixes

* more changes ([3f7012c](https://github.com/jakob1379/Canvas-Code-Correction/commits/3f7012c1c8504d3a70f076447e85aa386b6c771a))
* removed unwanted files ([9378557](https://github.com/jakob1379/Canvas-Code-Correction/commits/9378557fb24973ff97c04e161fcd473c6a08ac89))

### [1.1.1](https://github.com/jakob1379/Canvas-Code-Correction/compare/v1.1.0...v1.1.1) (2021-09-06)


### Bug Fixes

* removed unwanted files ([9378557](https://github.com/jakob1379/Canvas-Code-Correction/commits/9378557fb24973ff97c04e161fcd473c6a08ac89))

## 1.1.0 (2021-09-03)


### Features

* a minor version test ([5a833a2](https://github.com/jakob1379/Canvas-Code-Correction/commits/5a833a2a4fa928010b3f21082ade0b89dac3aee6))
* added hclustering to visualize plagiarism ([3e3e39c](https://github.com/jakob1379/Canvas-Code-Correction/commits/3e3e39c1130709d267fb1e649ae8f27902abbb21))
* converted functions to take canvas objects ([b6e5ee9](https://github.com/jakob1379/Canvas-Code-Correction/commits/b6e5ee99370cd4066465c343d24d8bd10a118c58))
* created readme and moved codebase to src folder ([569bf06](https://github.com/jakob1379/Canvas-Code-Correction/commits/569bf066d756e47e2346b4d9b3fdb260765697d5))
* minor ignore edit ([6ea6093](https://github.com/jakob1379/Canvas-Code-Correction/commits/6ea60937177996427001591ecb3dc3dbe2744353))


### Bug Fixes

* added url as a title in the mossum graph ([9d206f6](https://github.com/jakob1379/Canvas-Code-Correction/commits/9d206f6677b21f0aa4179e0a8715f389d7518c28))
* checked some boxes ([f1885c9](https://github.com/jakob1379/Canvas-Code-Correction/commits/f1885c95b1d7b291bae25e5a170564ac42a13746))
* now always writes a new config.ini ([4e1fd65](https://github.com/jakob1379/Canvas-Code-Correction/commits/4e1fd652c563a2d5d2368bd7371ca9f0221fb9d9))
* removed a lot of finished bullets ([48236ec](https://github.com/jakob1379/Canvas-Code-Correction/commits/48236ecdd7ab1d4df18c50819575e2d95c9241c4))
* removed newly ignored files ([ad07943](https://github.com/jakob1379/Canvas-Code-Correction/commits/ad0794383c896d918e3c53df29a7cea747039896))
* setup-assignmhnt-folders.sh->setup-assignment-folders.sh ([76b9289](https://github.com/jakob1379/Canvas-Code-Correction/commits/76b9289ea33df736c53671da338140cb8d5ee525))
* typo setup-assignmhnt-folders.sh -> setup-assignment-folders.sh ([7a08b7f](https://github.com/jakob1379/Canvas-Code-Correction/commits/7a08b7f2a86ea984e4d9e154215a69ca16d90235))
* updated counter in readme ([664f67e](https://github.com/jakob1379/Canvas-Code-Correction/commits/664f67eb7f9dc96021cbdbadd178ca880d3075e8))
