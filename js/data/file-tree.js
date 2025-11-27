// Evidence Drive File Tree Configuration
const FILE_BASE_PATH = 'C:/Users/pstep/OneDrive/Desktop/THE CASE';

const fileTree = {
    '': [
        { name: '00_MASTER_BUNDLE', type: 'folder', items: '11 files' },
        { name: '02_COURT_PROCEEDINGS_Hearings', type: 'folder', items: '14 folders' },
        { name: '02_COURT_PROCEEDINGS_Orders', type: 'folder', items: '1 folder' },
        { name: '02_COURT_PROCEEDINGS_Seamark_File', type: 'folder', items: '4 items' },
        { name: '02_COURT_PROCEEDINGS_Word_Docs', type: 'folder', items: 'Documents' },
        { name: '03_LEGAL_Appeal_PE23C50095', type: 'folder', items: 'Appeal docs' },
        { name: '03_LEGAL_Case_History_JFD_vs_SJS', type: 'folder', items: 'History' },
        { name: '04_EVIDENCE_Case_Notes', type: 'folder', items: 'Notes' },
        { name: '04_EVIDENCE_Downloaded_Materials', type: 'folder', items: 'Downloads' },
        { name: '04_EVIDENCE_General_Documents', type: 'folder', items: '12 folders' },
        { name: '04_EVIDENCE_Response_Notes', type: 'folder', items: 'Responses' },
        { name: '04_EVIDENCE_Threshold_Response', type: 'folder', items: 'Threshold' },
        { name: '05_PARTIES_CafCass', type: 'folder', items: '3 folders' },
        { name: '05_PARTIES_Dr_Hunnisett', type: 'folder', items: '2 folders' },
        { name: '05_PARTIES_Father_In_Law', type: 'folder', items: 'Documents' },
        { name: '05_PARTIES_JD', type: 'folder', items: 'Documents' },
        { name: '05_PARTIES_Local_Authority', type: 'folder', items: '12 folders' },
        { name: '05_PARTIES_Lucy_Ardern', type: 'folder', items: 'Guardian' },
        { name: '05_PARTIES_SJS', type: 'folder', items: '5 folders' },
        { name: '05_PARTIES_Solicitor_Confidential', type: 'folder', items: 'Legal' },
        { name: '06_COMMUNICATIONS_Emails', type: 'folder', items: 'Emails' },
        { name: '06_COMMUNICATIONS_Phone_Messages', type: 'folder', items: 'Messages' },
        { name: '07_INVESTIGATIONS_Defamation', type: 'folder', items: 'Investigation' },
        { name: '07_INVESTIGATIONS_MCU_Operation_Scan', type: 'folder', items: 'MCU' },
        { name: '08_CHILD_Ryan_Schooling_Health', type: 'folder', items: 'Ryan' },
        { name: '09_REFERENCE_Book_Materials', type: 'folder', items: 'Reference' },
        { name: '09_REFERENCE_NSPCC_Course', type: 'folder', items: 'Training' },
        { name: '10_ARCHIVE_2023', type: 'folder', items: 'Archive' },
        { name: '10_PERSONAL_Paul_Stephen', type: 'folder', items: 'Personal' }
    ],
    '00_MASTER_BUNDLE': [
        { name: '00_INDEX.pdf', ext: 'pdf' },
        { name: 'A_Preliminary_Documents.pdf', ext: 'pdf' },
        { name: 'B_Applications_Orders.pdf', ext: 'pdf' },
        { name: 'C_Statements_Affidavits.pdf', ext: 'pdf' },
        { name: 'D_Care_Plans.pdf', ext: 'pdf' },
        { name: 'E_Experts_Reports.pdf', ext: 'pdf' },
        { name: 'F_Miscellaneous.pdf', ext: 'pdf' },
        { name: 'G_Police_Disclosure.pdf', ext: 'pdf' },
        { name: 'H_Previous_Proceedings_PE22P31058.pdf', ext: 'pdf' },
        { name: 'I_Private_Law_PE23P30344.pdf', ext: 'pdf' },
        { name: 'J_Private_Law_PE21P30644.pdf', ext: 'pdf' }
    ],
    '05_PARTIES_CafCass': [
        { name: 'Guardian', type: 'folder', items: 'Documents' },
        { name: 'PDFS', type: 'folder', items: 'PDF files' },
        { name: 'WORD DOCS', type: 'folder', items: '6 files' }
    ],
    '05_PARTIES_CafCass/WORD DOCS': [
        { name: 'CAFCASS Report resp.docx', ext: 'docx' },
        { name: 'Cafcass 1 November 2022 simplified.docx', ext: 'docx' },
        { name: 'Cafcass Letter 17 Sept 2021 simplified.docx', ext: 'docx' },
        { name: 'Cafcass Letter 08 Apr 22 simplified.docx', ext: 'docx' },
        { name: 'Section 7 Report 28 Sept 2022.docx', ext: 'docx' },
        { name: 'cafcass 18 may 22.docx', ext: 'docx' }
    ],
    '05_PARTIES_Dr_Hunnisett': [
        { name: 'Recordings', type: 'folder', items: '6 audio + transcripts' },
        { name: 'transcripts', type: 'folder', items: '1 file' }
    ],
    '05_PARTIES_Dr_Hunnisett/Recordings': [
        { name: 'Paul Stephen Interview part 1.mp3', ext: 'mp3' },
        { name: 'Paul Stephen Interview part 2.mp3', ext: 'mp3' },
        { name: 'Paul Stephen Interview part 3.mp3', ext: 'mp3' },
        { name: 'Paul Stephen Interview part 4.mp3', ext: 'mp3' },
        { name: 'Samantha Stephen interview part 1.mp3', ext: 'mp3' },
        { name: 'Samantha Stephen interview part 2.mp3', ext: 'mp3' },
        { name: 'transcripts', type: 'folder', items: '6 files' }
    ],
    '05_PARTIES_Dr_Hunnisett/Recordings/transcripts': [
        { name: 'Paul Stephen Interview part 1.txt', ext: 'txt' },
        { name: 'Paul Stephen Interview part 2.txt', ext: 'txt' },
        { name: 'Paul Stephen Interview part 3.txt', ext: 'txt' },
        { name: 'Paul Stephen Interview part 4.txt', ext: 'txt' },
        { name: 'Samantha Stephen interview part 1.txt', ext: 'txt' },
        { name: 'Samantha Stephen interview part 2.txt', ext: 'txt' }
    ],
    '02_COURT_PROCEEDINGS_Orders': [
        { name: 'Orders', type: 'folder', items: '6 files' }
    ],
    '02_COURT_PROCEEDINGS_Orders/Orders': [
        { name: 'DunmoreStephenDraft CMO 19TH APRIL 2024_ LB changes (002) ML.pdf', ext: 'pdf' },
        { name: 'Official Iterim order 9June23.pdf', ext: 'pdf' },
        { name: 'Order July 19 2024.pdf', ext: 'pdf' },
        { name: 'Stephen-Dunmore - Order dated 9 June 2023.pdf', ext: 'pdf' },
        { name: 'police disclosure order private law 19.06.23.pdf', ext: 'pdf' }
    ],
    '05_PARTIES_Local_Authority': [
        { name: 'Assessments', type: 'folder', items: 'Documents' },
        { name: 'BUNDLE', type: 'folder', items: 'Bundle' },
        { name: 'Email - LA & IRO', type: 'folder', items: 'Emails' },
        { name: 'PDFS', type: 'folder', items: 'PDF files' },
        { name: 'PE23C50095 - CONTACT NOTES', type: 'folder', items: '13 files' },
        { name: 'PETER MEECH', type: 'folder', items: 'Documents' },
        { name: 'Sophie', type: 'folder', items: 'Documents' },
        { name: 'Suffolk', type: 'folder', items: 'Documents' },
        { name: 'WORD DOCS', type: 'folder', items: 'Documents' },
        { name: 'care plans', type: 'folder', items: 'Care plans' },
        { name: 'fran', type: 'folder', items: 'Documents' }
    ],
    '05_PARTIES_Local_Authority/PE23C50095 - CONTACT NOTES': [
        { name: '10-Apr-2024 11_52_Case Note for Dunmore, Ryan 04-Dec-2023.pdf', ext: 'pdf' },
        { name: 'Case Note for Stephen, Freya on 06-Dec-2023.pdf', ext: 'pdf' },
        { name: 'Case Note for Stephen, Freya on 18-Dec-2023.pdf', ext: 'pdf' },
        { name: 'Case Note for Stephen, Freya on 20-Dec-2023.pdf', ext: 'pdf' },
        { name: 'Case Notes for Ryan - August 2023_redacted.pdf', ext: 'pdf' },
        { name: 'Case Notes for Ryan - July 2023_redacted.pdf', ext: 'pdf' },
        { name: 'Supervised Contact Notes - Feb 2024.pdf', ext: 'pdf' },
        { name: 'Supervised Contact Notes - January 2024.pdf', ext: 'pdf' },
        { name: 'Supervised Contact Notes - March 2024.pdf', ext: 'pdf' },
        { name: 'Supervised Contact Notes - Ryan - November 2023.pdf', ext: 'pdf' },
        { name: 'Supervised Contact Notes - Ryan October 2023.pdf', ext: 'pdf' },
        { name: 'Supervised Contact Notes - Ryan September 2023.pdf', ext: 'pdf' },
        { name: 'Supervised contact notes 1 May to 14 August 2024.pdf', ext: 'pdf' }
    ],
    '02_COURT_PROCEEDINGS_Hearings': [
        { name: '02_COURT_PROCEEDINGS_Documents', type: 'folder', items: 'Documents' },
        { name: '1. 9 June 2023', type: 'folder', items: '3 files' },
        { name: '2. 19 June 2023', type: 'folder', items: 'Documents' },
        { name: '3. 5 October 2023', type: 'folder', items: 'Documents' },
        { name: '4. 27 October 2023', type: 'folder', items: 'Documents' },
        { name: '5. 15 December 2023', type: 'folder', items: 'Documents' },
        { name: '6. 9 February 2024', type: 'folder', items: 'Documents' },
        { name: '7. 26 February - 5 March', type: 'folder', items: 'Fact finding' },
        { name: '8. 15 March 2024', type: 'folder', items: 'Documents' },
        { name: '9. 19 April 2024', type: 'folder', items: 'Documents' },
        { name: '9 October 2024', type: 'folder', items: 'Documents' },
        { name: '26 September 2024', type: 'folder', items: 'Documents' },
        { name: 'mandy proceedings', type: 'folder', items: 'PGM hearings' }
    ],
    '02_COURT_PROCEEDINGS_Hearings/1. 9 June 2023': [
        { name: 'ORDER MADE BY HHJ GORDON-SAKER AT AN URGENT ICO HEARING ON THE 9TH JUNE 2023.docx', ext: 'docx' },
        { name: 'Position statement Sam 09.06.23.docx', ext: 'docx' }
    ],
    '05_PARTIES_SJS': [
        { name: 'Court Applications', type: 'folder', items: 'Applications' },
        { name: 'Court Position Statments', type: 'folder', items: 'Statements' },
        { name: 'Misc', type: 'folder', items: 'Documents' },
        { name: 'Police interviews', type: 'folder', items: 'Interviews' },
        { name: 'notes', type: 'folder', items: 'Notes' }
    ]
};
